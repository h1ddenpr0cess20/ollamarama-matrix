from __future__ import annotations

from typing import Any


async def handle_reset(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Reset history for a user in the current room.

    If the argument `stock` is provided, applies stock settings (no system
    prompt). Otherwise restores the default bot settings and system prompt.

    Args:
        ctx: Application context with `history`, `bot_id`, `render`, `matrix`,
            and `log`.
        room_id: Matrix room identifier where the command was received.
        sender_id: Fully qualified Matrix user ID of the sender.
        sender_display: Display name of the sender for messaging/logging.
        args: Optional argument, use `stock` to apply stock settings.

    Returns:
        None. Sends a confirmation message to the room.
    """
    stock = args.strip().lower() == "stock"
    ctx.history.reset(room_id, sender_id, stock=stock)
    if stock:
        body = f"Stock settings applied for {sender_display}"
        try:
            ctx.log(f"Stock settings applied for {sender_display} in {room_id}")
        except Exception:
            pass
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
    else:
        body = f"{ctx.bot_id} reset to default for {sender_display}"
        try:
            ctx.log(f"{ctx.bot_id} reset to default for {sender_display} in {room_id}")
        except Exception:
            pass
        await ctx.matrix.send_text(room_id, body, html=ctx.render(body))


async def handle_clear(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin: clear all histories and reset bot defaults.

    Clears conversation history for all rooms/users and restores the default
    model and personality.

    Args:
        ctx: Application context with `history`, `render`, `matrix`, and `log`.
        room_id: Matrix room identifier where the command was received.
        sender_id: Fully qualified Matrix user ID of the sender.
        sender_display: Display name of the sender (unused).
        args: Ignored for this command.

    Returns:
        None. Sends a confirmation message to the room.
    """
    ctx.history.clear_all()
    ctx.model = ctx.default_model
    ctx.personality = ctx.default_personality
    body = "Bot has been reset for everyone"
    try:
        ctx.log("Bot has been reset for everyone")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
