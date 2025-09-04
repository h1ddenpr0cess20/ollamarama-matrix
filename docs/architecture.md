# Architecture

The bot is a small, modular async application that wires a Matrix client to the Ollama Chat API through a command router and stateless handlers.

## Modules

- `ollamarama/cli.py`: CLI entry; validates config at startup and starts the app.
- `ollamarama/config.py`: Dataclasses, deep‑merge, validation, redacted summaries.
- `ollamarama/logging_conf.py`: Central logging setup with Rich handler, custom highlighter for Matrix context, and rich tracebacks.
- `ollamarama/ollama_client.py`: HTTP client for `/api/chat` and health checks.
- `ollamarama/matrix_client.py`: Thin wrapper over `nio.AsyncClient` (login/join/send/sync).
- `ollamarama/history.py`: Per‑room/user histories with prompt injection and trimming.
- `ollamarama/handlers/`: Router and command handlers (`.ai`, `.model`, `.reset`, `.help`, `.persona`, `.custom`, `.x`).
- `ollamarama/security.py`: To‑device callbacks and verification helpers.
- `ollamarama/interfaces.py`: Protocols for testing and typing.

## Data Flow

1. CLI loads and validates config; composes dependencies into an `AppContext`.
2. Matrix wrapper logs in, joins rooms, and dispatches text events to the router.
3. Router selects a handler by command prefix or `BotName:` mention.
4. Handlers read/write `HistoryStore` and call `OllamaClient` in a background thread.
5. Replies are sent with optional Markdown formatting.

## Async Boundaries

- Matrix I/O is async.
- Ollama HTTP calls are synchronous; they run in a thread executor via `ctx.to_thread`.

## Histories and Personas

The `HistoryStore` maintains a per‑user, per‑room transcript. A system prompt is always the first entry, constructed from the configured personality and prompt prefix/suffix. Trim logic ensures history stays within a fixed bound while keeping context fresh.

## Security Notes

- No secrets are committed. `config.json` lives locally.
- E2E is supported when `matrix-nio[e2e]` and libolm are present; store data under `store/` should be treated as sensitive.
- To‑device callbacks are registered to support device verification and logging.
