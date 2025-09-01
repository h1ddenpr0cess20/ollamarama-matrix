from __future__ import annotations

from typing import Any


async def handle_persona(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    persona = args.strip()
    ctx.history.init_prompt(room_id, sender_id, persona=persona)
    try:
        prompt = f"{ctx.history.prompt_prefix}{persona or ctx.history.personality}{ctx.history.prompt_suffix}"
        ctx.log(f"System prompt for {sender_id} set to '{prompt}'")
    except Exception:
        pass
    # Introduce self to seed the conversation
    ctx.history.add(room_id, sender_id, "user", "introduce yourself")
    await _respond(ctx, room_id, sender_id, sender_display)


async def handle_custom(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    custom = args.strip()
    if not custom:
        return
    ctx.history.init_prompt(room_id, sender_id, custom=custom)
    try:
        ctx.log(f"System prompt for {sender_id} set to '{custom}'")
    except Exception:
        pass
    ctx.history.add(room_id, sender_id, "user", "introduce yourself")
    await _respond(ctx, room_id, sender_id, sender_display)


async def _respond(ctx: Any, room_id: str, user_id: str, header_display: str) -> None:
    messages = ctx.history.get(room_id, user_id)
    try:
        data = await ctx.to_thread(
            ctx.ollama.chat, messages=messages, model=ctx.model, options=ctx.options, timeout=ctx.timeout
        )
    except Exception as e:
        try:
            await ctx.matrix.send_text(room_id, "Something went wrong", html=ctx.render("Something went wrong"))
            ctx.log(e)
        except Exception:
            pass
        return
    response_text = data.get("message", {}).get("content", "")
    # Log any thinking markers and ALWAYS strip from output
    if "</think>" in response_text and "<think>" in response_text:
        try:
            thinking, rest = response_text.split("</think>", 1)
            thinking = thinking.replace("<think>", "").strip()
            response_text = rest
            try:
                ctx.log(f"Model thinking for {user_id}: {thinking}")
            except Exception:
                pass
        except Exception:
            pass
    if "<|begin_of_thought|>" in response_text and "<|end_of_thought|>" in response_text:
        try:
            parts = response_text.split("<|end_of_thought|>")
            if len(parts) > 1:
                thinking = parts[0].replace("<|begin_of_thought|>", "").replace("<|end_of_thought|>", "").strip()
                response_text = parts[1]
                try:
                    ctx.log(f"Model thinking for {user_id}: {thinking}")
                except Exception:
                    pass
        except Exception:
            pass
    response_text = response_text.strip()
    ctx.history.add(room_id, user_id, "assistant", response_text)
    body = f"**{header_display}**:\n{response_text}"
    html = ctx.render(body)
    try:
        ctx.log(f"Sending response to {header_display} in {room_id}: {body}")
    except Exception:
        pass
    await ctx.matrix.send_text(room_id, body, html=html)
