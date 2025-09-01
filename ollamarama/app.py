from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

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
            # Log incoming user message with display + id
            try:
                ctx.log(f"{sender_display} ({sender}) sent {text} in {room.room_id}")  # type: ignore
            except Exception:
                pass
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
