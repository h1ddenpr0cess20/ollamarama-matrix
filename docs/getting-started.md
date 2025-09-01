# Getting Started

This guide gets you from zero to a running Matrix bot backed by Ollama.

## Prerequisites

- Python 3.8+
- A Matrix account for the bot (server URL, username, password)
- [Ollama](https://ollama.com/) installed and at least one model pulled

For a deeper Ollama configuration guide, see [Ollama Setup](ollama.md).

Install Ollama and a model:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen3
```

## Install Dependencies

Using the bundled requirements (includes E2E‑capable `matrix-nio[e2e]`):

```bash
pip install -r requirements.txt
```

If you cannot install E2E dependencies (libolm), you can run without E2E by installing minimal packages:

```bash
pip install matrix-nio markdown requests
```

## Configure

Create or edit `config.json` at the repo root:

```json
{
  "matrix": {
    "server": "https://matrix.org",
    "username": "@your_bot:matrix.org",
    "password": "your_password",
    "channels": ["#your-room:matrix.org"],
    "admins": ["Your Display Name"],
    "store_path": "store"
  },
  "ollama": {
    "api_url": "http://localhost:11434/api/chat",
    "models": {"qwen3": "qwen3"},
    "default_model": "qwen3",
    "prompt": ["you are ", "."],
    "personality": "a helpful assistant",
    "history_size": 24,
    "options": {"temperature": 0.8, "top_p": 1, "repeat_penalty": 1}
  },
  "markdown": true
}
```

See [Configuration](configuration.md) for the full schema and validation rules.

## Run

Preferred (installed command):

```bash
ollamarama-matrix --config config.json
```

Alternatively, run as a module:

```bash
python -m ollamarama --config config.json
```

Validate configuration without starting the bot:

```bash
ollamarama-matrix --dry-run -v
```

## Verify

- The bot logs in and joins configured rooms
- Send `.ai hello` or `BotName: hello` in a joined room
- The bot replies and maintains per‑user history
