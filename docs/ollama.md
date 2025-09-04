# Ollama Setup

This guide covers installing, configuring, and verifying Ollama for use with the Ollamarama Matrix bot.

## Install Ollama

- Download: <https://ollama.com/download>
- Default API: `http://localhost:11434`

Pull at least one model (example):

```bash
ollama pull qwen3
```

Tip: Any model ID available to your Ollama server can be used here (e.g., `llama3.1`, `qwen2.5`, `phi3`).

## Configure This Bot

Set the Ollama Chat API URL and default model in `config.json`:

```json
{
  "ollama": {
    "api_url": "http://localhost:11434/api/chat",
    "models": {"qwen3": "qwen3"},
    "default_model": "qwen3",
    "prompt": ["you are ", ".", "  keep your responses brief and to the point."],
    "personality": "a helpful assistant",
    "history_size": 24
  }
}
```

You can also override via environment variables:

- `OLLAMARAMA_OLLAMA_URL`: sets `ollama.api_url`
- `OLLAMARAMA_MODEL`: sets `ollama.default_model`

CLI helpers:

- `--ollama-url`: override the API URL
- `--model`: override the default model
- `-S, --server-models`: fetch available models from the server at startup
- `-v, --verbose`: enable verbose mode (omit brevity clause for new conversations)

See [CLI Reference](cli.md) and [Configuration](configuration.md) for details.

## Local vs. Remote

- Local (default): `http://localhost:11434/api/chat`
- Remote server: point `ollama.api_url` to the reachable host (e.g., `http://192.168.1.50:11434/api/chat`)
- On the server side, Ollama honors `OLLAMA_HOST` when you need to bind to a non‑localhost interface. For this bot’s client configuration, use `OLLAMARAMA_OLLAMA_URL` or the `--ollama-url` flag.

## Verify Connectivity

Check that the Ollama server is up and has models:

```bash
curl -s http://<host>:11434/api/tags | jq .
```

Minimal chat test (replace the model as needed):

```bash
curl -s http://<host>:11434/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
        "model": "qwen3",
        "messages": [
          {"role": "system", "content": "you are a helpful assistant."},
          {"role": "user", "content": "hello"}
        ]
      }' | jq .
```

Then run the bot:

```bash
ollamarama-matrix --config config.json
```

## Model Selection

- Configure a map of friendly names to model IDs under `ollama.models`.
- The `default_model` must match either a map key or an exact model ID.
- With `-S/--server-models`, the bot will prefer the models reported by your Ollama server. If the configured default is missing on the server, the launcher falls back to the first available model.

## Options

Per‑request options live under `ollama.options` in `config.json` (see [Configuration](configuration.md) for validation ranges):

- `temperature`, `top_p`, `repeat_penalty`, etc.

## HTTPS (Optional)

To access Ollama over HTTPS, run a local TLS proxy or terminate TLS on a reverse proxy (nginx/Caddy/Traefik) and point `ollama.api_url` to the HTTPS endpoint.

## Troubleshooting

- Models not found:
  - Ensure Ollama is running and `ollama list` shows the model.
  - Confirm `ollama.api_url` points to the correct host and includes `/api/chat`.
  - Use `-S/--server-models` to fetch and inspect the server’s view.
- No replies from the bot:
  - Verify the bot joined the room and that the Ollama API is reachable from this host.
  - Increase log detail: `OLLAMARAMA_LOG_LEVEL=DEBUG`.
- Timeouts / slow responses:
  - Try a smaller model.
  - Check server load; some models need more VRAM/CPU.
