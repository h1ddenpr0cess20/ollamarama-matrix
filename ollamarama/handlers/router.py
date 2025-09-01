from __future__ import annotations

import datetime as _dt
from typing import Callable, Dict, Optional, Tuple


class Router:
    """Command router mapping message prefixes to handlers.

    Handlers are callables with signature:
        handler(ctx, room_id: str, sender_id: str, sender_display: str, args: str) -> None|Awaitable

    The router itself is framework-agnostic; the surrounding code is expected to
    await handlers if they are coroutines.
    """

    def __init__(self) -> None:
        self._handlers: Dict[str, Callable] = {}
        self._admin_handlers: Dict[str, Callable] = {}

    def register(self, cmd: str, fn: Callable, admin: bool = False) -> None:
        """Register a handler for a command prefix.

        Args:
            cmd: Command keyword (e.g., `.ai`).
            fn: Callable to invoke for the command.
            admin: Whether the command requires admin privileges.

        Returns:
            None.
        """
        if admin:
            self._admin_handlers[cmd] = fn
        else:
            self._handlers[cmd] = fn

    def dispatch(
        self,
        ctx: object,
        room_id: str,
        sender_id: str,
        sender_display: str,
        text: str,
        is_admin: bool,
        bot_name: Optional[str] = None,
        timestamp: Optional[_dt.datetime] = None,
    ) -> Tuple[Optional[Callable], Tuple]:
        """Resolve a message into a handler and argument tuple.

        Matches the first token in the message against registered commands.
        If a `bot_name` is provided, also supports the mention form
        "Botname: message" by dispatching to `.ai`.

        Args:
            ctx: Opaque application context passed through to handlers.
            room_id: Matrix room identifier of the message.
            sender_id: Fully qualified Matrix user ID of the sender.
            sender_display: Display name of the sender.
            text: Raw message body.
            is_admin: Whether the sender has admin rights.
            bot_name: Optional display name for mention-style dispatch.
            timestamp: Optional timestamp for filtering (unused here).

        Returns:
            A tuple of (handler, args). If no handler matches, returns
            (None, ()).
        """
        parts = text.strip().split()
        if not parts:
            return None, tuple()
        cmd = parts[0]
        args = " ".join(parts[1:])
        # Bot mention form: "Botname: message"
        if bot_name and cmd == f"{bot_name}:":
            return self._handlers.get(".ai"), (ctx, room_id, sender_id, sender_display, args)

        if cmd in self._handlers:
            return self._handlers[cmd], (ctx, room_id, sender_id, sender_display, args)
        if is_admin and cmd in self._admin_handlers:
            return self._admin_handlers[cmd], (ctx, room_id, sender_id, sender_display, args)
        return None, tuple()
