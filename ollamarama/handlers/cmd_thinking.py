from __future__ import annotations

from typing import Any


async def handle_thinking(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin command to view or change the thinking placeholder.

    Usage: `.thinking [on|off|toggle]`.
    """
    arg = (args or "").strip().lower()
    if arg in ("", "status"):
        state = "ON" if getattr(ctx, "thinking", True) else "OFF"
        body = f"Thinking placeholder is **{state}**"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return

    new_state: bool | None = None
    if arg in ("on", "true", "1", "enable", "enabled"):
        new_state = True
    elif arg in ("off", "false", "0", "disable", "disabled"):
        new_state = False
    elif arg in ("toggle", "switch"):
        new_state = not bool(getattr(ctx, "thinking", True))
    else:
        body = "Usage: .thinking [on|off|toggle]"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return

    ctx.thinking = bool(new_state)
    state = "ON" if ctx.thinking else "OFF"
    body = f"Thinking placeholder set to **{state}**"
    try:
        ctx.log(body)
    except Exception:
        pass
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)
