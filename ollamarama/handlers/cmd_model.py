from __future__ import annotations

from typing import Any


async def handle_model(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Admin command to view or change the active model.

    Usage: `.model [name|reset]`.

    Without arguments, lists the current model and available model keys.
    With `reset`, restores the default model. Otherwise sets the model to
    the provided name or key.

    Args:
        ctx: Application context providing `models`, `model`, `default_model`,
            `render`, `matrix`, and `log`.
        room_id: Matrix room identifier where the command was received.
        sender_id: Fully qualified Matrix user ID of the sender.
        sender_display: Display name of the sender for logging.
        args: Optional model key/name or `reset`.

    Returns:
        None. Sends a status message to the room.
    """
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
