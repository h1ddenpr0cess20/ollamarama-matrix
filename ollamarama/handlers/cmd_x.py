from __future__ import annotations

from typing import Any


async def handle_x(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    # Expect: <target_display_name> <message>
    parts = (args or "").split()
    if len(parts) < 2:
        return
    target_display = parts[0]
    message = " ".join(parts[1:])

    # Try to resolve target by existing history keys or direct match
    target_user = None
    # Prefer exact user id if provided
    if target_display.startswith("@") and ":" in target_display:
        target_user = target_display
    else:
        # Search known users in this room by display name
        # Note: this is best-effort without room member list
        for user in list(ctx.history._messages.get(room_id, {}).keys()):  # type: ignore[attr-defined]
            name = await ctx.matrix.display_name(user)
            if name == target_display:
                target_user = user
                break
    # Only proceed if the target already has history in this room
    room_hist = getattr(ctx.history, "_messages", {}).get(room_id, {})  # type: ignore[attr-defined]
    if not target_user or target_user not in room_hist:
        return

    ctx.history.add(room_id, target_user, "user", message)
    try:
        data = await ctx.to_thread(
            ctx.ollama.chat, messages=ctx.history.get(room_id, target_user), model=ctx.model, options=ctx.options, timeout=ctx.timeout
        )
    except Exception as e:
        try:
            await ctx.matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return
    response_text = data.get("message", {}).get("content", "")
    # Log thinking markers
    if "</think>" in response_text and "<think>" in response_text:
        try:
            thinking, rest = response_text.split("</think>", 1)
            thinking = thinking.replace("<think>", "").strip()
            # Use provided target display name if available
            ctx.log(f"Model thinking for {target_display} ({target_user}): {thinking}")
            response_text = rest
        except Exception:
            pass
    if "<|begin_of_thought|>" in response_text and "<|end_of_thought|>" in response_text:
        try:
            parts = response_text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking = parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                ctx.log(f"Model thinking for {target_display} ({target_user}): {thinking}")
                response_text = parts[1]
        except Exception:
            pass
    response_text = response_text.strip()
    ctx.history.add(room_id, target_user, "assistant", response_text)
    body = f"**{sender_display}**:\n{response_text}"
    html = ctx.render(body)
    try:
        ctx.log(f"Sending response to {sender_display} in {room_id}: {body}")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=html)
