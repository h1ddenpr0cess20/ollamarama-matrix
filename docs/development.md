# Development Guide

## Project Structure

- Core bot: `ollamarama/` package (Matrix client wrapper, handlers, router, Ollama client).
- Config: `config.json` (Matrix creds, Ollama settings).
- Help text: `help.md` (user/admin commands shown in chat; split by `~~~`).
- Runtime data: `store/` (Matrix E2E state/keys), created automatically.
- Docs: `docs/` (overview, guides, references).

## Local Setup

- Install: `pip install -r requirements.txt`
- Run: `python -m ollamarama --config config.json`
- Optional linters: `ruff check .` and `black .`

## Coding Style

- PEP 8; 4‑space indentation; line length ≈ 100–120 chars.
- Names: functions/vars `snake_case`, classes `PascalCase`, constants `UPPER_SNAKE`.
- Prefer small async functions and pure helpers.
- Public functions should have docstrings and types where practical.
- Avoid wildcard imports; use the provided logger (`self.log`/`ctx.log`).

## Testing

- Framework: `pytest`. Tests live under `tests/` and follow `test_*.py`.
- Mock external I/O (`nio.AsyncClient`, HTTP calls to Ollama). The code exposes thin wrappers to simplify mocking.
- Target unit tests around:
  - Message parsing and router behavior
  - History trim/initialization
  - Model switching and prompt handling
- Aim for ≥80% coverage on changed code.

## Security & Configuration

- Do not commit secrets. Keep `config.json` out of version control.
- Keep `ollama.api_url` configurable; default stays local.
- Treat `store/` contents as sensitive if E2E is enabled.

## Contributing

- Use scoped, imperative commit messages (e.g., `fix: handle .x mentions`).
- Reference issues (e.g., `Closes #123`) and describe user impact.
- Keep diffs focused. Update docs and `help.md` when commands/flags change.
