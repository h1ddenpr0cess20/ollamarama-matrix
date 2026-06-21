from __future__ import annotations

from typing import Any


async def handle_history(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Toggle per-user history on or off.

    Usage: `.history [on|off|toggle]`
           `.history global [on|off|toggle|status]`  (admins only)

    When history is OFF, conversation history is cleared after each response
    so the next message starts with a fresh context (system prompt only).
    The global toggle overrides per-user settings for all users.
    """
    parts = (args or "").strip().lower().split()
    is_admin = sender_display in ctx.admins

    if parts and parts[0] == "global":
        if not is_admin:
            body = "Only admins can use `.history global`"
            await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
            return

        sub = parts[1] if len(parts) > 1 else ""
        if sub in ("", "status"):
            state = "OFF" if ctx.history.get_global_no_history() else "ON"
            body = f"Global history is **{state}**"
            await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
            return

        new_disabled: bool | None = None
        if sub in ("off", "false", "0", "disable", "disabled"):
            new_disabled = True
        elif sub in ("on", "true", "1", "enable", "enabled"):
            new_disabled = False
        elif sub in ("toggle", "switch"):
            new_disabled = not ctx.history.get_global_no_history()
        else:
            body = "Usage: .history global [on|off|toggle]"
            await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
            return

        ctx.history.set_global_no_history(new_disabled)
        state = "OFF" if new_disabled else "ON"
        body = f"Global history set to **{state}**"
        try:
            ctx.log(f"Global history set to {state} by {sender_display} ({sender_id}) in {room_id}")
        except Exception:
            pass
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    arg = parts[0] if parts else ""
    if arg in ("", "status"):
        state = "OFF" if ctx.history.get_no_history(room_id, sender_id) else "ON"
        body = f"History is **{state}** for {sender_display}"
        if ctx.history.get_global_no_history():
            body += " (global override is ON)"
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
        return

    new_disabled = None
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
    if new_disabled is False and ctx.history.get_global_no_history():
        body += " (note: global override is ON — history remains off for everyone)"
    try:
        ctx.log(f"History set to {state} for {sender_display} ({sender_id}) in {room_id}")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
