from __future__ import annotations

from typing import Any


async def handle_history(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Toggle per-user history on or off.

    Usage: `.history [on|off|toggle]`

    When history is OFF, conversation history is cleared after each response
    so the next message starts with a fresh context (system prompt only).
    """
    arg = (args or "").strip().lower()
    if arg in ("", "status"):
        state = "OFF" if ctx.history.get_no_history(room_id, sender_id) else "ON"
        body = f"History is **{state}** for {sender_display}"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    new_disabled: bool | None = None
    if arg in ("off", "false", "0", "disable", "disabled"):
        new_disabled = True
    elif arg in ("on", "true", "1", "enable", "enabled"):
        new_disabled = False
    elif arg in ("toggle", "switch"):
        new_disabled = not ctx.history.get_no_history(room_id, sender_id)
    else:
        body = "Usage: .history [on|off|toggle]"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    ctx.history.set_no_history(room_id, sender_id, new_disabled)
    state = "OFF" if new_disabled else "ON"
    body = f"History set to **{state}** for {sender_display}"
    try:
        ctx.log(f"History set to {state} for {sender_display} ({sender_id}) in {room_id}")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
