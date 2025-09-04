# Operations & Security

## Encryption (E2E)

- E2E requires `matrix-nio[e2e]` and libolm. When unavailable, run without E2E.
- Toggle with CLI flags `--e2e` / `--no-e2e` or via `matrix.e2e` in config.
- Persist the `store/` directory between runs to retain device keys; treat it as sensitive.
- See also: Device verification steps and behavior in [Verification](verification.md).

## Running the Bot

- Start: `ollamarama-matrix --config config.json`
- Log level: `--log-level DEBUG` or env `OLLAMARAMA_LOG_LEVEL=DEBUG`

### Logging

- Uses Rich for colorful logs and rich tracebacks by default.
- The console disables generic syntax highlighting (targeted styles only).
- The highlighter colors:
  - Display names/user IDs: cyan
  - Room IDs/aliases: magenta
  - “Thinking” details: dim italic
  - Response body: bold
  - Models and verification info: yellow/green

### Graceful Exit

- Stop the bot with Ctrl‑C (SIGINT) or send SIGTERM.
- The bot cancels the sync loop, logs out, closes the Matrix client, and shuts down worker threads.

## Health & Model

- Use `.model` to check current/available models and to change or reset.
- Use `OLLAMA_HOST`/`OLLAMARAMA_OLLAMA_URL` if your Ollama API is remote.
- Use `-S/--server-models` to populate the model list from the server at startup.

## Security Guidelines

- Do not commit secrets. Keep `config.json` local and redacted in tickets.
- Validate inputs; never echo credentials.
- Restrict bot admin to trusted display names via `matrix.admins`.

## Troubleshooting

- No replies: verify the bot joined the room and Ollama is reachable.
- E2E issues: ensure libolm is installed; try running without E2E to isolate.
- Model errors: confirm the model is pulled in Ollama and the ID matches.
- Markdown rendering problems: start with `"markdown": false` to isolate.
