# Operations & Security

## Encryption (E2E)

- E2E requires `matrix-nio[e2e]` and libolm. When unavailable, run without E2E.
- Toggle with CLI flags `--e2e` / `--no-e2e` or via `matrix.e2e` in config.
- Persist the `store/` directory between runs to retain device keys; treat it as sensitive.

## Running the Bot

- Start: `ollamarama-matrix --config config.json`
- Validate only: `ollamarama-matrix --dry-run -v`
- Log level: `--log-level DEBUG` (affects CLI launcher output)

## Health & Model

- Use `.model` to check current/available models and to change or reset.
- Use `OLLAMA_HOST`/`OLLAMARAMA_OLLAMA_URL` if your Ollama API is remote.

## Security Guidelines

- Do not commit secrets. Keep `config.json` local and redacted in tickets.
- Validate inputs; never echo credentials.
- Restrict bot admin to trusted display names via `matrix.admins`.

## Troubleshooting

- No replies: verify the bot joined the room and Ollama is reachable.
- E2E issues: ensure libolm is installed; try running without E2E to isolate.
- Model errors: confirm the model is pulled in Ollama and the ID matches.
- Markdown rendering problems: start with `"markdown": false` to isolate.
