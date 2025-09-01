from __future__ import annotations

from typing import Any


async def handle_help(ctx: Any, room_id: str, sender_id: str, sender_display: str, args: str) -> None:
    """Send the help menu to the room.

    Prefers `help.md` (rendered to HTML if Markdown is enabled) and falls back
    to `help.txt` or a short placeholder. If the help file contains sections
    split by `~~~`, the second section is only sent to admins.

    Args:
        ctx: Application context with `render`, `matrix`, and `admins`.
        room_id: Matrix room identifier where the command was received.
        sender_id: Fully qualified Matrix user ID of the sender.
        sender_display: Display name of the sender for admin checks.
        args: Ignored for this command.

    Returns:
        None. Sends one or two messages containing the help content.
    """
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
