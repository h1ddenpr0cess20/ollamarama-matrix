from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

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
        self.matrix = MatrixClientWrapper(
            server=cfg.matrix.server,
            username=cfg.matrix.username,
            password=cfg.matrix.password,
            device_id=cfg.matrix.device_id,
            store_path=cfg.matrix.store_path,
            encryption_enabled=bool(getattr(cfg.matrix, "e2e", True)),
        )
        self.ollama = OllamaClient(base_url=cfg.ollama.api_url.rsplit("/", 1)[0], timeout=cfg.ollama.timeout)
        self.history = HistoryStore(
            prompt_prefix=cfg.ollama.prompt[0],
            prompt_suffix=cfg.ollama.prompt[1],
            personality=cfg.ollama.personality,
            max_items=cfg.ollama.history_size,
        )
        # Expose commonly used fields
        self.models = cfg.ollama.models
        self.default_model = cfg.ollama.default_model
        self.model = cfg.ollama.default_model
        self.default_personality = cfg.ollama.personality
        self.personality = cfg.ollama.personality
        self.options = cfg.ollama.options
        self.timeout = cfg.ollama.timeout
        self.admins = cfg.matrix.admins
        self.bot_id = "Ollamarama"
        # Tool calling
        self.tools_enabled: bool = True
        self.mcp_client: FastMCPClient | None = None
        self._mcp_tool_names: set[str] = set()
        try:
            builtin_schema = load_schema()
        except Exception:
            builtin_schema = []
        mcp_schema: List[Dict[str, Any]] = []
        if cfg.ollama.mcp_servers:
            successful: Dict[str, Any] = {}
            for name, cfg_spec in cfg.ollama.mcp_servers.items():
                if not cfg_spec:
                    continue
                try:
                    client = FastMCPClient({name: cfg_spec})
                    tools = client.list_tools()
                    successful[name] = cfg_spec
                    mcp_schema.extend(tools)
                    for tool in tools:
                        fn = (tool.get("function") or {}).get("name")
                        if isinstance(fn, str):
                            self._mcp_tool_names.add(fn)
                except Exception:
                    continue
            if successful:
                try:
                    self.mcp_client = FastMCPClient(successful)
                    _ = self.mcp_client.list_tools()
                except Exception:
                    self.mcp_client = None
        combined: List[Dict[str, Any]] = list(mcp_schema)
        for tool in builtin_schema:
            fn = (tool.get("function") or {}).get("name")
            if isinstance(fn, str) and fn not in self._mcp_tool_names:
                combined.append(tool)
        self.tools_schema = combined
        if not self.tools_schema:
            self.tools_enabled = False

    async def to_thread(self, fn, *args, **kwargs) -> Any:
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
        if self.mcp_client is not None and name in self._mcp_tool_names:
            return self.mcp_client.call_tool(name, arguments)
        return execute_tool(name, arguments)

    def respond_with_tools(self, messages: List[Dict[str, Any]], *, tool_choice: str | None = "auto") -> str:
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
            return ""
        max_iterations = 8
        iterations = 0
        while iterations < max_iterations:
            msg = result.get("message", {})
            tool_calls = msg.get("tool_calls") or []
            if not tool_calls:
                break
            messages.append(msg)
            for call in tool_calls:
                func = (call.get("function") or {})
                name = func.get("name") or ""
                raw_args = func.get("arguments")
                try:
                    if isinstance(raw_args, str):
                        import json as _json

                        args = _json.loads(raw_args) if raw_args.strip() else {}
                    elif isinstance(raw_args, dict):
                        args = raw_args
                    else:
                        args = {}
                except Exception:
                    args = {}
                tool_result = self._execute_tool(name, args)
                tool_msg: Dict[str, Any] = {
                    "role": "tool",
                    "content": str(tool_result),
                }
                if call.get("id"):
                    tool_msg["tool_call_id"] = call["id"]
                messages.append(tool_msg)
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
                return ""
            iterations += 1
        final = result.get("message", {})
        content = final.get("content", "").strip()
        messages.append({"role": "assistant", "content": content})
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
        return content


import json
from typing import Optional


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

    ctx.log(f"Model set to {ctx.model}")
    # Load store, login, and initial sync
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

    # Persist device_id if missing in config and available from client
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

    # Join rooms
    for room in cfg.matrix.channels:
        try:
            await ctx.matrix.join(room)
            ctx.log(f"{ctx.bot_id} joined {room}")
        except Exception:
            ctx.log(f"Couldn't join {room}")

    import datetime as _dt
    # Security: to-device callbacks and allowance
    security = Security(ctx.matrix, logger=ctx.logger)
    try:
        # Register callbacks for to-device events and verification
        try:
            from nio import KeyVerificationEvent  # type: ignore
        except Exception:  # pragma: no cover
            KeyVerificationEvent = None  # type: ignore
        ctx.matrix.add_to_device_callback(security.emoji_verification_callback, (KeyVerificationEvent,) if KeyVerificationEvent else None)
        ctx.matrix.add_to_device_callback(security.log_to_device_event, None)
    except Exception:
        pass

    join_time = _dt.datetime.now()

    async def on_text(room, event) -> None:
        """Handle incoming text events from Matrix and dispatch commands."""
        try:
            message_time = getattr(event, "server_timestamp", 0) / 1000.0
            message_time = _dt.datetime.fromtimestamp(message_time)
            if message_time <= join_time:
                return
            text = getattr(event, "body", "")
            sender = getattr(event, "sender", "")
            # Ignore our own messages
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
            # Log only messages relevant to bot commands (after dispatch)
            try:
                ctx.log(f"{sender_display} ({sender}) sent {text} in {room.room_id}")  # type: ignore
            except Exception:
                pass
            # Attempt to allow devices for this sender before handling
            try:
                await security.allow_devices(sender)
            except Exception:
                pass
            res = handler(*args)
            if asyncio.iscoroutine(res):
                await res
        except Exception as e:
            ctx.log(e)

    ctx.matrix.add_text_handler(on_text)

    # Graceful shutdown: handle SIGINT/SIGTERM and race with sync task
    import signal as _signal
    stop = asyncio.Event()
    try:
        loop = asyncio.get_running_loop()
        for sig in (_signal.SIGINT, _signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, stop.set)
            except Exception:
                # Not supported on some platforms or threads
                pass
    except Exception:
        pass

    sync_task = asyncio.create_task(ctx.matrix.sync_forever())
    stop_task = asyncio.create_task(stop.wait())
    try:
        done, pending = await asyncio.wait({sync_task, stop_task}, return_when=asyncio.FIRST_COMPLETED)
    except KeyboardInterrupt:
        # Fallback path if signals aren't available
        pass
    finally:
        # If stop was triggered, cancel sync; if sync finished, just proceed
        for t in (sync_task, stop_task):
            if not t.done():
                t.cancel()
        # Best-effort client shutdown
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
