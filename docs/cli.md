# CLI Reference

Use the installed command (preferred):

`ollamarama-matrix [flags]`

Or run the module directly:

`python -m ollamarama [flags]`

## Flags

- `-c, --config PATH`: Path to `config.json` (default: `./config.json`).
- `-L, --log-level LEVEL`: `DEBUG|INFO|WARNING|ERROR|CRITICAL` (colored Rich logs).
- `-S, --server-models`: Fetch available models from the Ollama server and use them instead of `ollama.models` from config. If the configured `default_model` is not present on the server, the launcher prefers `qwen3` if available; otherwise falls back to the first available model.
- `-d, --dry-run`: Load, merge overrides, validate config, and exit.
- `-v, --verbose`: With `--dry-run`, print redacted effective config.
- Overrides:
  - `-E, --e2e` / `-N, --no-e2e`
  - `-m, --model`
  - `-s, --store-path`
  - `-u, --ollama-url`
  - `-t, --timeout`
  - `-M, --no-markdown`

## Examples

- Validate config:
  - `ollamarama-matrix --dry-run -v`
- Validate with overrides:
  - `ollamarama-matrix --dry-run --model qwen3 --ollama-url http://localhost:11434/api/chat`
 - Fetch models from server:
   - `ollamarama-matrix -S --config config.json`
 - Run with verbose colored logs:
   - `OLLAMARAMA_LOG_LEVEL=DEBUG ollamarama-matrix --config config.json`

## Exit Codes

- 0: OK
- 2: Configuration error or file load failure
