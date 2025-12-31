"""Runtime entry points for the Matrix bot."""

from __future__ import annotations

import asyncio
import datetime as _dt
import json
from typing import Any, Callable, Optional

from .app_context import AppContext
from .app_router import _build_router
from .config import AppConfig
from .handlers.router import Router
from .security import Security


async def _persist_device_id_if_needed(ctx: AppContext, cfg: AppConfig, config_path: Optional[str]) -> None:
    """Persist a discovered device ID back to the configuration file.

    Args:
        ctx: Application context.
        cfg: Application configuration.
        config_path: Path to the configuration file, if provided.
    """
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
    """Join all configured Matrix rooms.

    Args:
        ctx: Application context.
        cfg: Application configuration.
    """
    for room in cfg.matrix.channels:
        try:
            await ctx.matrix.join(room)
            ctx.log(f"{ctx.bot_id} joined {room}")
        except Exception:
            ctx.log(f"Couldn't join {room}")


def _register_security_callbacks(ctx: AppContext) -> Security:
    """Register security callbacks for verification and logging.

    Args:
        ctx: Application context.

    Returns:
        Security helper wired to Matrix callbacks.
    """
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
    """Create a stop event and register SIGINT/SIGTERM handlers.

    Returns:
        asyncio.Event used to signal shutdown.
    """
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
    """Run the sync loop until stopped or sync completes.

    Args:
        ctx: Application context.
        stop: Event to signal shutdown.
    """
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
    join_time: _dt.datetime,
) -> Callable[[Any, Any], Any]:
    """Build the text event handler for Matrix messages.

    Args:
        ctx: Application context.
        cfg: Application configuration.
        router: Command router.
        security: Security helper for device checks.
        join_time: Timestamp of bot join for filtering old events.

    Returns:
        Async callback that handles text events.
    """

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


__all__ = ["run"]
