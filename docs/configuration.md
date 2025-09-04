# Configuration

Ollamarama reads a JSON configuration file (default `./config.json`). You can override the path with `--config` or the `OLLAMARAMA_CONFIG` environment variable. CLI flags and selected environment variables are merged on top of the file.

## Schema

- matrix:
  - server (url)
  - username, password
  - channels: list of room aliases/ids (e.g., `"#room:server"`, `"!roomid:server"`)
  - admins: list of display names with admin privileges
  - device_id: optional; persisted after first login
  - store_path: directory for Matrix store (default: `store`)
  - e2e: boolean, enable end‑to‑end encryption (default: true)
- ollama:
  - api_url: Chat endpoint (default: `http://localhost:11434/api/chat`)
  - models: mapping of friendly names to model IDs (e.g., `{ "qwen3": "qwen3" }`)
  - default_model: selected model (must match a key or ID)
  - prompt: two strings `[prefix, suffix]` used around personality
  - personality: non‑empty default personality text
  - history_size: 1–1000 messages retained per user per room
  - options: advanced generation options (e.g., `temperature`, `top_p`, `repeat_penalty`)
  - mcp_servers: mapping of names to MCP server specs for tool calling (optional)
- markdown: render replies as Markdown (default: true)

## Overrides

- CLI flags: `--e2e/--no-e2e`, `--ollama-url`, `--model`, `--store-path`, `--no-markdown`
- Environment variables:
  - `OLLAMARAMA_OLLAMA_URL`
  - `OLLAMARAMA_MODEL`
  - `OLLAMARAMA_STORE_PATH`
  - `OLLAMARAMA_MATRIX_SERVER`

## Validation

The CLI dry‑run validates the configuration and prints a redacted summary with `-v`.

```bash
python -m ollamarama --dry-run -v
```

Validation checks:

- `matrix.server` is a valid http(s) URL
- Credentials and channels are present and well‑formed
- `ollama.default_model` is non‑empty and present by key or ID
- `ollama.prompt` is a 2‑element list of strings
- Bounds on `options` (temperature 0–2, top_p 0–1, repeat_penalty 0.5–2)
