from __future__ import annotations

from typing import Any


async def handle_reset(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
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
    ctx.history.clear_all()
    ctx.model = ctx.default_model
    ctx.personality = ctx.default_personality
    body = "Bot has been reset for everyone"
    try:
        ctx.log("Bot has been reset for everyone")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=ctx.render(body))
