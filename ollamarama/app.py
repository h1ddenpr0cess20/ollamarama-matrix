from __future__ import annotations

import json
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Callable, Tuple

from .config import AppConfig
from .history import HistoryStore
from .matrix_client import MatrixClientWrapper
from .ollama_client import OllamaClient
from .handlers.router import Router
from .handlers.cmd_ai import handle_ai
from .handlers.cmd_model import handle_model
from .handlers.cmd_reset import handle_reset, handle_clear
from .handlers.cmd_help import handle_help
from .handlers.cmd_prompt import handle_persona, handle_custom
from .handlers.cmd_x import handle_x
from .security import Security
from .fastmcp_client import FastMCPClient
from .tools import execute_tool, load_schema


class AppContext:
    """Holds application-wide dependencies for handlers.

    Not yet used by the runtime path; prepared for future integration.
    """

    def __init__(self, cfg: AppConfig, executor: Optional[ThreadPoolExecutor] = None) -> None:
        self.cfg = cfg
        self.executor = executor or ThreadPoolExecutor(max_workers=4, thread_name_prefix="ollama")
        self.logger = logging.getLogger(__name__)
        # Convenience: info-level callable
        self.log = self.logger.info
        self._suppress_noisy_logs()
        self.matrix = self._build_matrix_client(cfg)
        self.ollama = self._build_ollama_client(cfg)
        self.history = self._build_history_store(cfg)
        self._expose_config_fields(cfg)
        self._configure_verbose_mode(cfg)
        self._init_tool_calling(cfg)

    def _suppress_noisy_logs(self) -> None:
        try:
            for logger_name in ("fastmcp", "mcp", "mcp.server", "mcp.client", "openai.mcp"):
                logging.getLogger(logger_name).setLevel(logging.ERROR)
        except Exception:
            pass

    def _build_matrix_client(self, cfg: AppConfig) -> MatrixClientWrapper:
        return MatrixClientWrapper(
            server=cfg.matrix.server,
            username=cfg.matrix.username,
            password=cfg.matrix.password,
            device_id=cfg.matrix.device_id,
            store_path=cfg.matrix.store_path,
            encryption_enabled=bool(getattr(cfg.matrix, "e2e", True)),
        )

    def _build_ollama_client(self, cfg: AppConfig) -> OllamaClient:
        return OllamaClient(base_url=cfg.ollama.api_url.rsplit("/", 1)[0], timeout=cfg.ollama.timeout)

    def _build_history_store(self, cfg: AppConfig) -> HistoryStore:
        # Support optional third prompt element used as a brevity clause
        prompt_parts = list(cfg.ollama.prompt or ["you are ", "."])
        prefix = prompt_parts[0] if len(prompt_parts) >= 1 else "you are "
        suffix = prompt_parts[1] if len(prompt_parts) >= 2 else "."
        extra = prompt_parts[2] if len(prompt_parts) >= 3 else ""
        return HistoryStore(
            prompt_prefix=prefix,
            prompt_suffix=suffix,
            personality=cfg.ollama.personality,
            prompt_suffix_extra=extra,
            max_items=cfg.ollama.history_size,
        )

    def _expose_config_fields(self, cfg: AppConfig) -> None:
        self.models = cfg.ollama.models
        self.default_model = cfg.ollama.default_model
        self.model = cfg.ollama.default_model
        self.default_personality = cfg.ollama.personality
        self.personality = cfg.ollama.personality
        self.options = cfg.ollama.options
        self.timeout = cfg.ollama.timeout
        self.admins = cfg.matrix.admins
        self.bot_id = "Ollamarama"

    def _configure_verbose_mode(self, cfg: AppConfig) -> None:
        try:
            self.verbose = bool(getattr(cfg.ollama, "verbose", False))
        except Exception:
            self.verbose = False
        try:
            self.history.set_verbose(self.verbose)
        except Exception:
            pass

    def _load_builtin_tools_schema(self) -> List[Dict[str, Any]]:
        try:
            return load_schema()
        except Exception:
            self.logger.exception("Failed to load builtin tools schema")
            return []

    def _probe_mcp_tools(self, cfg: AppConfig) -> Tuple[List[Dict[str, Any]], set[str], FastMCPClient | None]:
        if not cfg.ollama.mcp_servers:
            return [], set(), None

        self.logger.info("MCP servers configured: %s", list(cfg.ollama.mcp_servers.keys()))
        mcp_schema: List[Dict[str, Any]] = []
        tool_names: set[str] = set()
        successful: Dict[str, Any] = {}

        for name, cfg_spec in cfg.ollama.mcp_servers.items():
            if not cfg_spec:
                continue
            try:
                self.logger.debug("Probing MCP server '%s' for tools", name)
                client = FastMCPClient({name: cfg_spec})
                tools = client.list_tools()
                self.logger.info("MCP server '%s' returned %d tool(s)", name, len(tools))
                successful[name] = cfg_spec
                mcp_schema.extend(tools)
                for tool in tools:
                    fn = (tool.get("function") or {}).get("name")
                    if isinstance(fn, str):
                        tool_names.add(fn)
            except Exception:
                self.logger.exception("Failed to list tools from MCP server '%s'", name)

        if not successful:
            return mcp_schema, tool_names, None

        try:
            consolidated = FastMCPClient(successful)
            _ = consolidated.list_tools()
            self.logger.debug("Initialized consolidated MCP client for servers: %s", list(successful.keys()))
            return mcp_schema, tool_names, consolidated
        except Exception:
            self.logger.exception("Failed to initialize consolidated MCP client")
            return mcp_schema, tool_names, None

    def _init_tool_calling(self, cfg: AppConfig) -> None:
        self.tools_enabled = True
        builtin_schema = self._load_builtin_tools_schema()
        mcp_schema, mcp_tool_names, mcp_client = self._probe_mcp_tools(cfg)

        self.mcp_client = mcp_client
        self._mcp_tool_names = mcp_tool_names

        combined: List[Dict[str, Any]] = list(mcp_schema)
        for tool in builtin_schema:
            fn = (tool.get("function") or {}).get("name")
            if isinstance(fn, str) and fn not in self._mcp_tool_names:
                combined.append(tool)
        self.tools_schema = combined

        if not self.tools_schema:
            self.tools_enabled = False
            self.logger.info("Tool calling disabled: no tools available")
            return

        self.logger.info(
            "Tool calling enabled with %d tools (%d MCP, %d builtin)",
            len(self.tools_schema),
            len(mcp_schema),
            len(self.tools_schema) - len(mcp_schema),
        )

    async def to_thread(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Run a blocking function in the background thread pool.

        Args:
            fn: Callable to execute.
            *args: Positional arguments for the callable.
            **kwargs: Keyword arguments for the callable.

        Returns:
            The result returned by the callable.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, lambda: fn(*args, **kwargs))

    def render(self, body: str) -> Optional[str]:
        """Render Markdown to HTML if Markdown is enabled.

        Args:
            body: Message body in Markdown.

        Returns:
            Rendered HTML if Markdown is enabled and rendering succeeds;
            otherwise ``None``.
        """
        if not self.cfg.markdown:
            return None
        try:
            import markdown as _md

            return _md.markdown(
                body,
                extensions=["extra", "fenced_code", "nl2br", "sane_lists", "tables", "codehilite"],
            )
        except Exception:
            return None

    def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> str:
        log = getattr(self, "logger", logging.getLogger(__name__))
        # Prepare concise, safe parameter logging
        try:
            _args_str = json.dumps(arguments or {}, ensure_ascii=False, default=str)
        except Exception:
            _args_str = str(arguments)
        # Truncate for readability
        if len(_args_str) > 800:
            _args_str = _args_str[:800] + "…"
        if self.mcp_client is not None and name in self._mcp_tool_names:
            log.info("Tool (MCP): %s args=%s", name, _args_str)
            return self.mcp_client.call_tool(name, arguments)
        log.info("Tool (builtin): %s args=%s", name, _args_str)
        return execute_tool(name, arguments)

    def _parse_tool_arguments(self, raw_args: Any, *, tool_name: str) -> Dict[str, Any]:
        log = getattr(self, "logger", logging.getLogger(__name__))
        try:
            if isinstance(raw_args, str):
                return json.loads(raw_args) if raw_args.strip() else {}
            if isinstance(raw_args, dict):
                return raw_args
        except Exception:
            log.exception("Failed to parse tool arguments for '%s'", tool_name)
        return {}

    def _prune_tool_messages(self, messages: List[Dict[str, Any]]) -> None:
        messages[:] = [
            m
            for m in messages
            if not (m.get("role") == "tool" or (isinstance(m, dict) and m.get("tool_calls")))
        ]
        if len(messages) > 24:
            if messages and messages[0].get("role") == "system":
                messages.pop(1)
            else:
                messages.pop(0)

    def respond_with_tools(self, messages: List[Dict[str, Any]], *, tool_choice: str | None = "auto") -> str:
        log = getattr(self, "logger", logging.getLogger(__name__))
        try:
            result = self.ollama.chat_with_tools(
                model=self.model,
                messages=messages,
                options=self.options,
                tools=self.tools_schema,
                tool_choice=tool_choice,
                timeout=self.timeout,
            )
        except Exception:
            log.exception("Initial chat_with_tools failed")
            return ""

        max_iterations = 8
        iterations = 0
        while iterations < max_iterations:
            msg = result.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break

            try:
                log.info("Model requested %d tool call(s)", len(tool_calls))
                log.debug("Requested tools: %s", [(tc.get("function") or {}).get("name") for tc in tool_calls])
            except Exception:
                pass

            messages.append(msg)
            for call in tool_calls:
                func = call.get("function") or {}
                name = func.get("name") or ""
                args = AppContext._parse_tool_arguments(self, func.get("arguments"), tool_name=name)

                tool_result = self._execute_tool(name, args)
                tool_msg: Dict[str, Any] = {"role": "tool", "content": str(tool_result)}
                if call.get("id"):
                    tool_msg["tool_call_id"] = call["id"]
                messages.append(tool_msg)

            log.debug("Executed %d tool call(s)", len(tool_calls))
            try:
                result = self.ollama.chat_with_tools(
                    model=self.model,
                    messages=messages,
                    options=self.options,
                    tools=self.tools_schema,
                    tool_choice=tool_choice,
                    timeout=self.timeout,
                )
            except Exception:
                log.exception("Follow-up chat_with_tools failed")
                return ""
            iterations += 1

        final = result.get("message", {})
        content = final.get("content", "").strip()
        messages.append({"role": "assistant", "content": content})
        AppContext._prune_tool_messages(self, messages)
        log.debug("Responded with %d characters after %d iteration(s)", len(content), iterations)
        return content


def _build_router() -> Router:
    router = Router()
    # user commands
    router.register(".ai", handle_ai)
    router.register(".x", handle_x)
    router.register(".persona", handle_persona)
    router.register(".custom", handle_custom)
    router.register(".reset", handle_reset)
    router.register(".stock", lambda c, r, s, d, a: handle_reset(c, r, s, d, "stock"))
    router.register(".help", handle_help)
    # admin commands
    router.register(".model", handle_model, admin=True)
    router.register(".clear", handle_clear, admin=True)
    try:
        from .handlers.cmd_verbose import handle_verbose

        router.register(".verbose", handle_verbose, admin=True)
    except Exception:
        pass
    return router


async def _persist_device_id_if_needed(ctx: AppContext, cfg: AppConfig, config_path: Optional[str]) -> None:
    try:
        device_id = getattr(ctx.matrix.client, "device_id", None)
        if device_id and hasattr(cfg.matrix, "device_id") and not cfg.matrix.device_id and config_path:
            with open(config_path, "r+") as f:
                data = json.load(f)
                data.setdefault("matrix", {})["device_id"] = device_id
                f.seek(0)
                json.dump(data, f, indent=4)
                f.truncate()
            ctx.log(f"Persisted device_id to {config_path}")
    except Exception:
        pass


async def _join_rooms(ctx: AppContext, cfg: AppConfig) -> None:
    for room in cfg.matrix.channels:
        try:
            await ctx.matrix.join(room)
            ctx.log(f"{ctx.bot_id} joined {room}")
        except Exception:
            ctx.log(f"Couldn't join {room}")


def _register_security_callbacks(ctx: AppContext) -> Security:
    security = Security(ctx.matrix, logger=ctx.logger)
    try:
        try:
            from nio import KeyVerificationEvent  # type: ignore
        except Exception:  # pragma: no cover
            KeyVerificationEvent = None  # type: ignore
        ctx.matrix.add_to_device_callback(
            security.emoji_verification_callback,
            (KeyVerificationEvent,) if KeyVerificationEvent else None,
        )
        ctx.matrix.add_to_device_callback(security.log_to_device_event, None)
    except Exception:
        pass
    return security


def _setup_stop_event() -> asyncio.Event:
    import signal as _signal

    stop = asyncio.Event()
    try:
        loop = asyncio.get_running_loop()
        for sig in (_signal.SIGINT, _signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except Exception:
                pass
    except Exception:
        pass
    return stop


async def _run_until_stopped(ctx: AppContext, stop: asyncio.Event) -> None:
    sync_task = asyncio.create_task(ctx.matrix.sync_forever())
    stop_task = asyncio.create_task(stop.wait())
    try:
        await asyncio.wait({sync_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    except KeyboardInterrupt:
        pass
    finally:
        for t in (sync_task, stop_task):
            if not t.done():
                t.cancel()


def _make_text_handler(
    ctx: AppContext,
    cfg: AppConfig,
    router: Router,
    security: Security,
    join_time,
):
    import datetime as _dt

    async def on_text(room, event) -> None:
        try:
            message_time = getattr(event, "server_timestamp", 0) / 1000.0
            message_time = _dt.datetime.fromtimestamp(message_time)
            if message_time <= join_time:
                return
            text = getattr(event, "body", "")
            sender = getattr(event, "sender", "")
            if sender == cfg.matrix.username:
                return

            sender_display = await ctx.matrix.display_name(sender)
            is_admin = sender_display in ctx.admins
            handler, args = router.dispatch(
                ctx,
                room.room_id,  # type: ignore
                sender,
                sender_display,
                text,
                is_admin,
                bot_name=ctx.bot_id,
                timestamp=message_time,
            )
            if handler is None:
                return
            try:
                ctx.log(f"{sender_display} ({sender}) sent {text} in {room.room_id}")  # type: ignore
            except Exception:
                pass
            try:
                await security.allow_devices(sender)
            except Exception:
                pass
            res = handler(*args)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            ctx.log(e)

    return on_text


async def run(cfg: AppConfig, config_path: Optional[str] = None) -> None:
    """Start the Matrix bot using the provided configuration.

    Sets up the application context, registers command handlers, connects to
    the Matrix server, joins configured rooms, and processes messages until
    interrupted. Persists the device ID to `config_path` if discovered.

    Args:
        cfg: Fully validated application configuration.
        config_path: Optional path to the configuration file for persisting
            a discovered device ID.

    Returns:
        None. Runs until stop signal or sync completion.
    """
    ctx = AppContext(cfg)
    router = _build_router()

    ctx.log(f"Model set to {ctx.model}")
    await ctx.matrix.load_store()
    login_resp = await ctx.matrix.login()
    try:
        ctx.log(login_resp)
    except Exception:
        pass
    await ctx.matrix.ensure_keys()
    await ctx.matrix.initial_sync()

    # Determine bot display name
    try:
        ctx.bot_id = await ctx.matrix.display_name(cfg.matrix.username)
    except Exception:
        ctx.bot_id = cfg.matrix.username

    await _persist_device_id_if_needed(ctx, cfg, config_path)

    await _join_rooms(ctx, cfg)

    security = _register_security_callbacks(ctx)
    import datetime as _dt

    join_time = _dt.datetime.now()
    ctx.matrix.add_text_handler(_make_text_handler(ctx, cfg, router, security, join_time))

    stop = _setup_stop_event()
    try:
        await _run_until_stopped(ctx, stop)
    finally:
        # Best-effort client shutdown and background cleanup
        try:
            if hasattr(ctx.matrix, "shutdown"):
                await ctx.matrix.shutdown()
        except Exception:
            pass
        # Stop background executor threads
        try:
            ctx.executor.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
