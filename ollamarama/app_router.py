"""Command router factory for the application."""

from __future__ import annotations

from .handlers.cmd_ai import handle_ai
from .handlers.cmd_help import handle_help
from .handlers.cmd_history import handle_history
from .handlers.cmd_model import handle_model
from .handlers.cmd_prompt import handle_custom, handle_persona
from .handlers.cmd_reset import handle_clear, handle_reset
from .handlers.cmd_x import handle_x
from .handlers.router import Router


def _build_router() -> Router:
    """Build and register the command router.

    Returns:
        Router configured with user and admin commands.
    """
    router = Router()
    router.register(".ai", handle_ai)
    router.register(".x", handle_x)
    router.register(".persona", handle_persona)
    router.register(".custom", handle_custom)
    router.register(".reset", handle_reset)
    router.register(".stock", lambda c, r, s, d, a: handle_reset(c, r, s, d, "stock"))
    router.register(".history", handle_history)
    router.register(".help", handle_help)
    router.register(".model", handle_model, admin=True)
    router.register(".clear", handle_clear, admin=True)
    try:
        from .handlers.cmd_verbose import handle_verbose

        router.register(".verbose", handle_verbose, admin=True)
    except Exception:
        # The .verbose command is optional; an older install without the
        # handler module simply does not expose it.
        pass
    try:
        from .handlers.cmd_thinking import handle_thinking

        router.register(".thinking", handle_thinking, admin=True)
    except Exception:
        # The .thinking command is optional; an older install without the
        # handler module simply does not expose it.
        pass
    return router


__all__ = ["_build_router"]
