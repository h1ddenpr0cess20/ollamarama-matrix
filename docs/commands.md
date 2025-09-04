# Commands

Users can interact with the bot using dot‑commands or by mentioning the bot name followed by a colon.

## User Commands

- `.ai <message>` or `BotName: <message>` — Chat with the AI (calls tools automatically when configured).
- `.x <display_name|@user:server> <message>` — Continue another user’s conversation.
- `.persona <text>` — Set or change your personality for the system prompt.
- `.custom <prompt>` — Replace the system prompt with a custom one.
- `.reset` — Clear your history and reset to the default personality.
- `.stock` — Clear your history and run without a system prompt.
- `.help` — Show help text (admin section shown only to admins).

## Admin Commands

- `.model [name|reset]` — Show/change the active model. `reset` restores default.
- `.clear` — Reset the bot globally for all users.

Tip: Admin privileges are based on the sender display name matching one of the configured `matrix.admins` entries.
