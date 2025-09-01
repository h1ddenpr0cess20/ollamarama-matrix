from __future__ import annotations

from typing import Any


async def handle_model(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin: `.model [name|reset]`"""
    arg = (args or "").strip()
    if not arg:
        # Show current model and available model keys (friendly names)
        keys = []
        try:
            keys = sorted(list(ctx.models)) if isinstance(ctx.models, dict) else sorted(list(ctx.models))
        except Exception:
            pass
        body = f"**Current model**: {ctx.model}\n**Available models**: {', '.join(keys)}"
        html = ctx.render(body)
        await ctx.matrix.send_text(room_id, body, html=html)
        return
    if arg == "reset":
        ctx.model = ctx.default_model
        ctx.log(f"Model set to {ctx.model}")

    else:
        # Allow key lookup if dict
        try:
            if isinstance(ctx.models, dict) and arg in ctx.models:
                ctx.model = ctx.models[arg]
            else:
                ctx.model = arg
        except Exception:
            pass

    body = f"Model set to **{ctx.model}**"
    ctx.log(body)
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)
