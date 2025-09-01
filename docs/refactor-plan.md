# Refactor Blueprint (Historical)

This document captures the modular refactor plan that guided the current implementation. It is preserved for reference.

## Objectives

- Separate concerns: CLI, config, Matrix I/O, Ollama HTTP, handlers, history, logging
- Typed interfaces and dependency injection for testability
- Robust configuration precedence (CLI > ENV > file > defaults)
- Focused tests and thorough documentation

## Target Package Layout

- `ollamarama/__main__.py`: Entrypoint wiring CLI → app
- `ollamarama/cli.py`: Arg parsing and runtime options
- `ollamarama/app.py`: Compose config/clients/handlers; start loop
- `ollamarama/config.py`: Dataclasses, deep‑merge, validation
- `ollamarama/logging_conf.py`: `setup_logging(level, json=False)`
- `ollamarama/ollama_client.py`: HTTP client (`chat`, `health`) with timeouts
- `ollamarama/matrix_client.py`: Thin wrapper over `nio.AsyncClient`
- `ollamarama/history.py`: Per‑room/user transcripts, prompt injection, trimming
- `ollamarama/handlers/`: `router.py`, `cmd_ai.py`, `cmd_model.py`, `cmd_reset.py`, `cmd_help.py`, `cmd_prompt.py`, `cmd_x.py`
- `ollamarama/security.py`: Verification helpers and to‑device callbacks
- `ollamarama/interfaces.py`: Protocols for clients/stores
- `ollamarama/exceptions.py`: Typed errors
