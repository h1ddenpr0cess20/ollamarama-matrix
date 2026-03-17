# Docker

This guide covers building and running the Ollamarama Matrix bot with Docker and Docker Compose. The image is minimal, E2E‑ready (libolm installed), and runs as a non‑root user, persisting sensitive state under `/data`.

## Prerequisites

- Docker 20.10+
- Optional: Docker Compose v2 (`docker compose`)
- A Matrix account for the bot and a `config.json` (see Configuration)

## Build the Image

Build from the repo root:

```bash
docker build -t ollamarama-matrix:latest .
```

What's inside:

- Installs Python dependencies from `requirements.txt`
- Includes `libolm3` for end‑to‑end encryption support
- Uses a non‑root `app` user and stores data under `/data`
- Defaults: `OLLAMARAMA_CONFIG=/data/config.json`, `OLLAMARAMA_STORE_PATH=/data/store`

## Run with Docker

1) Prepare configuration and store directories on the host:

```bash
mkdir -p store
cp config.json ./config.json  # ensure it contains Matrix creds, rooms, models
```

2) Run the container with `--network host` so it can reach Ollama and any local MCP servers on the host:

```bash
docker run --rm -it \
  --name ollamarama \
  --network host \
  -v "$(pwd)/config.json":/data/config.json:ro \
  -v "$(pwd)/store":/data/store \
  -e OLLAMARAMA_LOG_LEVEL=INFO \
  ollamarama-matrix:latest
```

Notes:

- In PowerShell, use backticks (`` ` ``) for line continuation—or place the command on a single line—otherwise the trailing `\` characters above will trigger `docker: invalid reference format`. Example:

```powershell
docker run --rm -it `
  --name ollamarama `
  --network host `
  -v "${PWD}/config.json:/data/config.json:ro" `
  -v "${PWD}/store:/data/store" `
  -e OLLAMARAMA_LOG_LEVEL=INFO `
  ollamarama-matrix:latest
```

- `--network host` shares the host's network stack with the container, so `localhost` URLs in your config (Ollama, MCP servers) work directly.
- The bot does not expose ports; it connects out to Matrix and Ollama.
- Persist `/data/store` to retain device keys for E2E rooms.

## Run with Docker Compose

This repo includes a `docker-compose.yml` that starts both Ollama and the bot.

1) Ensure your `config.json` is present at the repo root and contains Matrix credentials, channels, and model selection. The compose file uses `network_mode: host` for the bot so localhost URLs (Ollama, MCP servers) work directly.

2) Start services:

```bash
docker compose up -d --build
```

By default the compose file runs the bot container with your host UID and GID for easier file permissions when writing to `./store`.
If your user is not `1000:1000`, export matching values before starting compose:

```bash
export UID=$(id -u)
export GID=$(id -g)
docker compose up -d --build
```

3) Follow logs:

```bash
docker compose logs -f bot
```

By default, compose mounts:

- `./config.json` → `/data/config.json:ro`
- `./store` → `/data/store` (persist E2E keys)

The `ollama` service publishes `11434` on the host. Pull models on the server:

```bash
docker exec -it ollama ollama pull qwen3
```

### GPU (optional)

If you have NVIDIA GPUs, install the NVIDIA Container Toolkit and uncomment the `deploy.resources.reservations.devices` stanza under the `ollama` service in `docker-compose.yml`.

## MCP Servers

Local MCP servers work in Docker thanks to `--network host` (or `network_mode: host` in Compose), which shares the host's network stack with the container. Any MCP server running on the host and configured with a `localhost` or `127.0.0.1` URL in `config.json` is reachable without extra setup.

For stdio/command‑based MCP servers (e.g. `uvx`, `npx`), the binary must be installed inside the container image. Prefer URL‑based MCP servers when running in Docker.

## Configuration

- File: mount your `config.json` at `/data/config.json` (read‑only recommended).
- Overrides: you can override selected fields via environment variables:
  - `OLLAMARAMA_OLLAMA_URL` → `ollama.api_url`
  - `OLLAMARAMA_MODEL` → `ollama.default_model`
  - `OLLAMARAMA_STORE_PATH` → `matrix.store_path` (defaults to `/data/store` in the image)
  - `OLLAMARAMA_MATRIX_SERVER` → `matrix.server`

See [Configuration](configuration.md) for the full schema and validation rules.

## Security Notes

- The container runs as a non‑root user and stores encryption state under `/data`.
- Treat `store/` as sensitive; back it up securely and do not commit it.
- Keep `config.json` outside the image and mount it read‑only.

## Troubleshooting

- No replies: check `docker logs -f ollamarama` and verify Ollama is reachable.
- E2E errors: ensure `/data/store` is writable and persisted; try running without E2E to isolate.
- Models missing: pull the model in the `ollama` container or point `OLLAMARAMA_OLLAMA_URL` to a server with the model.
- Increase verbosity: set `-e OLLAMARAMA_LOG_LEVEL=DEBUG`.
