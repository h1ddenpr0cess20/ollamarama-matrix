# Legacy → New Mapping

This page maps parts of the archived legacy implementation to their equivalents in the refactored codebase.

## Startup & Runtime

- Legacy `legacy/ollamarama.py: main()` → New `ollamarama/__main__.py` (entry), `ollamarama/cli.py` (flags, dry‑run), `ollamarama/app.py: run()` (compose, login/join/sync).
- Legacy direct `config.json` read → New `ollamarama/config.py` (`load_config`, `AppConfig`, `validate_config`, `summarize`).
- Legacy logging via `logging.basicConfig` → New `ollamarama/logging_conf.py: setup_logging()` and `AppContext.logger`.

## Matrix I/O

- Legacy `AsyncClient` setup, `room_send` in `send_message()` → New `ollamarama/matrix_client.py: MatrixClientWrapper` (`login`, `join`, `send_text`, `display_name`, `sync_forever`).
- Legacy event callbacks `message_callback` → New `app.py: on_text()` registered with `MatrixClientWrapper.add_text_handler()`.

## Routing & Commands

- Legacy `handle_message()` dict of commands → New `ollamarama/handlers/router.py: Router` with `register()` and `dispatch()`.
- Legacy “BotName:” mention handled inline → New `Router.dispatch()` supports `bot_name` and routes to `.ai`.

## AI Interaction

- Legacy `respond()` building payload and `requests.post` → New `ollamarama/ollama_client.py: OllamaClient.chat()`; called via `ctx.to_thread` from handlers.
- Legacy stripping `<think>`, `<|begin_of_thought|>`, `<|begin_of_solution|>` → New logic in `handlers/cmd_ai.py: handle_ai()` and `handlers/cmd_prompt.py: _respond()`.

## History & Personas

- Legacy `messages` dict + `add_history()` + trim → New `ollamarama/history.py: HistoryStore` (`add`, `get`, `reset`, `init_prompt`, `_trim`).
- Legacy `set_prompt(persona/custom)` → New `handlers/cmd_prompt.py: handle_persona()` and `handle_custom()`.

## User Commands

- Legacy `.ai` / `BotName:` → New `handlers/cmd_ai.py: handle_ai()`.
- Legacy `.x` cross‑user → New `handlers/cmd_x.py: handle_x()` (display name → user resolution for known histories).
- Legacy `.reset` and `.stock` → New `handlers/cmd_reset.py: handle_reset()`.
- Legacy `.help` (split by `~~~`) → New `handlers/cmd_help.py: handle_help()`.

## Admin Commands

- Legacy `.model` (list/set/reset) → New `handlers/cmd_model.py: handle_model()`.
- Legacy `.clear` → New `handlers/cmd_reset.py: handle_clear()`.

## Security & E2E

- Legacy `VerificationMixin`, key upload, `add_to_device_callback` → New `ollamarama/security.py: Security` (to‑device logging, best‑effort device allow) wired in `app.py`; keys via `MatrixClientWrapper.ensure_keys()`.

## Join/Time & Self‑Ignorance

- Legacy `join_time` filter, ignore self → New `app.py: on_text()` compares `server_timestamp` to `join_time` and skips `cfg.matrix.username`.

## Markdown Rendering

- Legacy inline Markdown in `send_message()` → New `AppContext.render()`; handlers call `MatrixClientWrapper.send_text()` with `body` and `html`.

## Model/Options/Timeouts

- Legacy embedded options/timeouts → New config (`ollamarama/config.py`), exposed on `AppContext` (`model`, `models`, `default_model`, `options`, `timeout`).

## Device ID Persistence

- Legacy writeback after login → New `app.py: run()` persists `device_id` into `config.json` when provided (`config_path`).

## Documentation

- Legacy top‑level docs → New consolidated under `docs/` (index, getting started, configuration, commands, architecture, CLI, operations, development, migration, refactor plan).
- `help.md` remains at repo root; consumed by `handlers/cmd_help.py`.
