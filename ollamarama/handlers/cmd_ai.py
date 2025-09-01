from __future__ import annotations

from typing import Any


async def handle_ai(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Handle `.ai` or mention form messages.

    Expects `ctx` to provide:
      - history: HistoryStore
      - ollama: OllamaClient
      - matrix: MatrixClientWrapper
      - model: str
      - options: dict
    """
    history = ctx.history
    matrix = ctx.matrix
    ollama = ctx.ollama

    if args:
        history.add(room_id, sender_id, "user", args)
    messages = history.get(room_id, sender_id)

    try:
        data = await ctx.to_thread(ollama.chat, messages=messages, model=ctx.model, options=ctx.options, timeout=ctx.timeout)
    except Exception as e:
        try:
            await matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return

    response_text = data.get("message", {}).get("content", "")
    # Strip think tags if present
    if "</think>" in response_text and "<think>" in response_text:
        try:
            thinking, rest = response_text.split("</think>", 1)
            thinking = thinking.replace("<think>", "").strip()
            ctx.log(f"Model thinking for {sender_id}: {thinking}")
            response_text = rest
        except Exception:
            pass
    if "<|begin_of_thought|>" in response_text and "<|end_of_thought|>" in response_text:
        try:
            parts = response_text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking = parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                ctx.log(f"Model thinking for {sender_id}: {thinking}")
                response_text = parts[1]
        except Exception:
            pass
    if "<|begin_of_solution|>" in response_text and "<|end_of_solution|>" in response_text:
        try:
            response_text = response_text.split("<|begin_of_solution|>", 1)[1].split("<|end_of_solution|>", 1)[0].strip()
        except Exception:
            pass

    response_text = response_text.strip()
    history.add(room_id, sender_id, "assistant", response_text)
    body = f"**{sender_display}**:\n{response_text}"
    html = ctx.render(body)
    try:
        ctx.log(f"Sending response to {sender_display} in {room_id}: {body}")
    except Exception:
        pass
    await matrix.send_text(room_id, body, html=html)
