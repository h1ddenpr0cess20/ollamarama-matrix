from __future__ import annotations

from typing import Any


async def handle_help(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    # Prefer Markdown help; fall back to legacy txt if needed
    help_menu = ""
    for path in ("help.md", "help.txt"):
        try:
            with open(path, "r") as f:
                help_menu = f.read()
                break
        except Exception:
            continue
    if not help_menu:
        help_menu = "See README for usage."
    # Split on ~~~ if present and send admin section only to admins
    parts = help_menu.split("~~~")
    body = parts[0]
    html = ctx.render(body)
    await ctx.matrix.send_text(room_id, body, html=html)
    if sender_display in getattr(ctx, "admins", []):
        if len(parts) > 1:
            body2 = parts[1]
            html2 = ctx.render(body2)
            await ctx.matrix.send_text(room_id, body2, html=html2)
