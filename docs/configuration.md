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
  - prompt: two strings `[prefix, suffix]` used around personality; optionally a third string for a brevity clause `[prefix, suffix, brevity]`
  - personality: non‑empty default personality text
  - history_size: 1–1000 messages retained per user per room
  - options: advanced generation options (e.g., `temperature`, `top_p`, `repeat_penalty`)
  - verbose: boolean, when true omit the optional brevity clause for new conversations
  - mcp_servers: mapping of names to MCP server specs for tool calling (optional)
    - Accepts multiple formats per server:
      - String URL: `"http://localhost:9000"`
      - Shell string: `"uvx my-mcp-server --port 9000"`
      - List argv: `["uvx", "my-mcp-server", "--port", "9000"]`
      - Dict: `{ "command": "uvx", "args": ["my-mcp-server", "--port", "9000"] }`
      - Dict with embedded args: `{ "command": "uvx my-mcp-server --port 9000" }`
      - Dict URL alias: `{ "url": "http://localhost:9000" }`
    - Notes:
      - The app normalizes these forms and will log which servers are configured.
      - Server processes started via `command` have their stderr suppressed to reduce noise.
      - You may also place `mcp_servers` at the top level of the config; it will be merged into `ollama.mcp_servers` for backward compatibility.
- markdown: render replies as Markdown (default: true)

## Overrides

- CLI flags: `--e2e/--no-e2e`, `--ollama-url`, `--model`, `--store-path`
- Environment variables:
  - `OLLAMARAMA_OLLAMA_URL`
  - `OLLAMARAMA_MODEL`
  - `OLLAMARAMA_STORE_PATH`
  - `OLLAMARAMA_MATRIX_SERVER`

## Validation

The application validates configuration on startup; on errors it prints messages and exits with code `2`.

Validation checks:

- `matrix.server` is a valid http(s) URL
- Credentials and channels are present and well‑formed
- `ollama.default_model` is non‑empty and present by key or ID
- `ollama.prompt` is a list of 2 or 3 strings
- Bounds on `options` (temperature 0–2, top_p 0–1, repeat_penalty 0.5–2)
 - `ollama.mcp_servers` must be a mapping if provided
