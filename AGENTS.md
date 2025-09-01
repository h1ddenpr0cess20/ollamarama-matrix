# Repository Guidelines

## Project Structure & Module Organization

- `ollamarama/`: application code (CLI, config, Matrix/Ollama clients, security, history). Command handlers live in `ollamarama/handlers/` (e.g., `cmd_ai.py`, `cmd_model.py`, `router.py`).
- `docs/`: user and operator docs (getting started, commands, security, architecture).
- `tests/`: pytest suite covering CLI, handlers, routing, config, security, and orchestration.
- Top-level: `config.json` (example), `help.md` (rendered help), `README.md`, policy docs.

## Build, Test, and Development Commands

- Create venv: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `pip install -r requirements.txt`
- Run tests: `pytest -q`
- Run locally: `ollamarama-matrix --config config.json`
- Editable install (optional): `pip install -e .`

## Coding Style & Naming Conventions

- Python 3.8+; 4‑space indentation; prefer clear names and small, focused modules.
- Files and modules: `snake_case.py`. Handlers prefixed `cmd_*.py`.
- Functions/variables: `lower_snake_case`; classes: `CapWords`.
- Type hints where useful; avoid unnecessary dependencies.
- Markdown: keep tidy (e.g., fix blank lines around lists). Help is formatted with headings/tables (no bullets).

## Testing Guidelines

- Frameworks: `pytest`, `pytest-asyncio` for async handlers and clients.
- Naming: files `tests/test_*.py`; tests `test_*` functions or `Test*` classes.
- Scope: add tests alongside behavior changes; prefer small, deterministic cases.
- Examples: `tests/test_handlers_model_ai_help.py`, `tests/test_router_more.py`.

## Commit & Pull Request Guidelines

- Commits: present-tense, concise, scoped (e.g., “Add model reset in handler”).
- PRs: describe problem and solution; list minimal changes; include/adjust tests; update docs if behavior changes.
- Keep PRs focused (no unrelated refactors); do not commit secrets or credentials.

## Security & Configuration Tips

- Read `SECURITY.md` and `docs/security.md` for hardening and reporting.
- Use a dedicated bot account; verify devices for E2EE rooms.
- Protect `config.json` (e.g., `chmod 600`); avoid logging sensitive content; set a `store` path to persist encryption state.

