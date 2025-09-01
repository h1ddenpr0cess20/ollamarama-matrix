# CLI Reference

Use the installed command (preferred):

`ollamarama-matrix [flags]`

Or run the module directly:

`python -m ollamarama [flags]`

## Flags

- `--config PATH`: Path to `config.json` (default: `./config.json`).
- `--log-level LEVEL`: `DEBUG|INFO|WARNING|ERROR|CRITICAL` (launcher only).
- `--dry-run`: Load, merge overrides, validate config, and exit.
- `-v, --verbose`: With `--dry-run`, print redacted effective config.
- Overrides: `--e2e/--no-e2e`, `--model`, `--store-path`, `--ollama-url`, `--timeout`, `--no-markdown`.

## Examples

- Validate config:
  - `ollamarama-matrix --dry-run -v`
- Validate with overrides:
  - `ollamarama-matrix --dry-run --model qwen3 --ollama-url http://localhost:11434/api/chat`

## Exit Codes

- 0: OK
- 2: Configuration error or file load failure
