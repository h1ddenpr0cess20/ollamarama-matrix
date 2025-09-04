from __future__ import annotations

from typing import Any


async def handle_verbose(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin command to view or change verbose mode.

    Usage: `.verbose [on|off|toggle]`.

    When verbose mode is ON, the optional brevity clause (third prompt element)
    is omitted from new conversations and resets. Existing conversations are
    not modified.
    """
    arg = (args or "").strip().lower()
    if arg in ("", "status"):
        state = "ON" if getattr(ctx, "verbose", False) else "OFF"
        body = f"Verbose mode is **{state}**"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return

    new_state: bool | None = None
    if arg in ("on", "true", "1", "enable", "enabled"):
        new_state = True
    elif arg in ("off", "false", "0", "disable", "disabled"):
        new_state = False
    elif arg in ("toggle", "switch"):
        new_state = not bool(getattr(ctx, "verbose", False))
    else:
        body = "Usage: .verbose [on|off|toggle]"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return

    ctx.verbose = bool(new_state)
    try:
        ctx.history.set_verbose(ctx.verbose)
    except Exception:
        pass
    state = "ON" if ctx.verbose else "OFF"
    body = f"Verbose mode set to **{state}**"
    try:
        ctx.log(body)
    except Exception:
        pass
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)

