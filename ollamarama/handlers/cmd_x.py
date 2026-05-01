from __future__ import annotations

from typing import Any


async def handle_x(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Send a message on behalf of one user to another.

    Expects arguments in the form: `<target_display_name> <message>`. The
    target is resolved by exact display name match among users with existing
    history in the room, or by a provided user ID. The model response is
    appended to the target user's history.

    Args:
        ctx: Application context with `history`, `matrix`, `ollama`, `model`,
            `options`, `timeout`, and `render`.
        room_id: Matrix room identifier where the command was received.
        sender_id: Fully qualified Matrix user ID of the sender.
        sender_display: Display name of the sender for display in the reply.
        args: Target display name and message body.

    Returns:
        None. Sends a response message to the room if the target is resolved.
    """
    raw = (args or "").strip()
    if not raw:
        return

    target_user = None
    target_display = ""
    message = ""

    # Explicit mxid target: `.x @user:server message`
    if raw.startswith("@"):
        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            return
        possible_user, rest = parts
        if ":" in possible_user:
            target_user = possible_user
            target_display = possible_user
            message = rest

    # Display-name target (supports spaces): choose the longest matching name
    if not target_user:
        candidates = []
        for user in list(ctx.history._messages.get(room_id, {}).keys()):  # type: ignore[attr-defined]
            name = await ctx.matrix.display_name(user)
            if not name:
                continue
            if raw == name:
                candidates.append((len(name), user, name, ""))
            elif raw.startswith(f"{name} "):
                candidates.append((len(name), user, name, raw[len(name) + 1 :]))

        if not candidates:
            return
        _, target_user, target_display, message = max(candidates, key=lambda c: c[0])
        if not message:
            return

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
            await ctx.send_response(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
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
    await ctx.send_response(room_id, body, html=html)
