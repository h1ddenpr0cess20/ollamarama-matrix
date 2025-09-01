# Contributing

Thanks for your interest. This repository is primarily a learning project. Small, focused contributions that fix real bugs or improve clarity are welcome.

## What’s Welcome

- Bug fixes with clear reproduction steps and a minimal patch.
- Tests that increase coverage of existing behavior.
- Small documentation tweaks that improve accuracy or clarity.

## What’s Not a Fit

- New features or large refactors (unless discussed and agreed in advance).
- Off‑topic discussions (political/ideological/social). Keep it technical.
- Drive‑by formatting churn or unrelated file cleanups.

## Development Setup

- Requirements: Python 3.11+, `pip`, and a virtual environment.
- Install deps:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
  - `pip install pytest pytest-asyncio`
- Editable install (optional): `pip install -e .`

## Running Tests

- Run the suite: `pytest -q`
- Focus a test: `pytest -q tests/test_foo.py::test_bar`
- Please include tests for bug fixes when feasible.

## Project Conventions

- Python: prefer clear names, type hints where they add value, and minimal dependencies.
- Keep changes small and focused; avoid unrelated edits.
- CLI name in docs/examples: `ollamarama-matrix`.
- Docs: keep Markdown tidy (e.g., fix blank lines around lists per MD032).
- Do not commit secrets or credentials. Configuration examples belong in `config*.json` templates.

## How to Contribute

1. Fork the repo and create a topic branch.
2. Reproduce the issue and confirm the root cause.
3. Make a minimal change that fixes the problem; add/adjust tests.
4. Run `pytest -q` to verify.
5. Open a pull request describing:
   - The bug and steps to reproduce
   - The minimal fix you applied
   - Any notes on limitations or follow‑ups

## Reporting Issues

- Include environment info (Python version, OS), steps to reproduce, expected vs actual behavior, and relevant logs.
- Security issues: please avoid public issues; contact the maintainer privately or open a GitHub security advisory if available.

## License

- By contributing, you agree that your contributions are licensed under AGPL‑3.0, consistent with this repository’s LICENSE.
