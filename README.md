# ollamarama-matrix

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Matrix Protocol](https://img.shields.io/badge/chat-Matrix-green.svg)](https://matrix.org/)
[![Ollama](https://img.shields.io/badge/AI-Ollama-orange.svg)](https://ollama.com/)
[![GitHub](https://img.shields.io/github/stars/h1ddenpr0cess20/ollamarama-matrix?style=social)](https://github.com/h1ddenpr0cess20/ollamarama-matrix)

Ollamarama is a powerful AI chatbot for the Matrix chat protocol powered by the Ollama Chat API. Transform your Matrix rooms with an AI that can roleplay as virtually anything you can imagine — privately, locally, and fast.

## Documentation

- [Overview](docs/index.md)
- [Getting Started](docs/getting-started.md)
- [Configuration](docs/configuration.md)
- [Commands](docs/commands.md)
- [CLI Reference](docs/cli.md)
- [Operations & E2E](docs/operations.md)
- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Migration](docs/migration.md)
- [Legacy Map](docs/legacy-map.md)
- [Security](docs/security.md)
- [AI Output Disclaimer](docs/ai-output-disclaimer.md)

## Features

- Dynamic personalities with quick switching
- Per‑user history, isolated per room and user
- Collaborative mode to talk across histories
- Admin controls for model switching and resets
- Custom system prompts for specialized tasks

## Related Projects

- IRC version: <https://github.com/h1ddenpr0cess20/ollamarama-irc>
- CLI version: <https://github.com/h1ddenpr0cess20/ollamarama>

## Installation

Options depending on how you prefer to run it:

- From source (installs CLI):
  - Clone this repo, then run: `pip install .`
  - Or use pipx for isolation: `pipx install .`
- From source without installing the package:
  - `pip install -r requirements.txt`
  - Run with: `python -m ollamarama --config config.json`

After installation, use the `ollamarama-matrix` command. For E2E encryption, ensure `libolm` is installed; see [Operations & E2E](docs/operations.md).

## Quick Start

### Prerequisites

Install and familiarize yourself with Ollama to run local LLMs.

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Pull at least one model (recommended):

```bash
ollama pull qwen3
```

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure

Create or edit `config.json` at the repo root. See [Configuration](docs/configuration.md) for a minimal example, full schema, and validation guidance.

### 3) Run

Preferred (installed command):

```bash
ollamarama-matrix --config config.json
```

Fetch models from the server (ignores `ollama.models` in config):

```bash
ollamarama-matrix --config config.json --server-models
```

Short form:

```bash
ollamarama-matrix -S --config config.json
```

Validate only (no network login):

```bash
ollamarama-matrix --dry-run -v
```

Alternatively, run as a module:

```bash
python -m ollamarama --config config.json
```

### 4) Try It

- The bot logs in and joins configured rooms
- Send `.ai hello` or `BotName: hello` in a joined room
- The bot replies and maintains per‑user history

## Logging

- Uses `rich` for colorful, readable logs by default.
- Configure verbosity with `--log-level` or `OLLAMARAMA_LOG_LEVEL` (e.g., `DEBUG`, `INFO`).
- Automatically falls back to standard logging if `rich` is unavailable.

## Usage Guide

Common commands (see [Commands](docs/commands.md) for the full list):

| Command | Description | Example |
|---------|-------------|---------|
| `.ai <message>` or `botname: <message>` | Chat with the AI | `.ai Hello there!` |
| `.x <user> <message>` | Continue another user's conversation | `.x Alice What did we discuss?` |
| `.persona <text>` | Change your personality | `.persona helpful librarian` |
| `.custom <prompt>` | Use a custom system prompt | `.custom You are a coding expert` |
| `.reset` / `.stock` | Clear history (default/stock prompt) | `.reset` |
| `.model [name]` (admin) | Show/change model | `.model qwen3` |
| `.clear` (admin) | Reset globally for all users | `.clear` |

## Encryption Support

- Works in encrypted Matrix rooms using `matrix-nio[e2e]` with device verification.
- Requires `libolm` available to Python for E2E. If unavailable, you can run without E2E; see [Getting Started](docs/getting-started.md) (Install Dependencies).
- Persist the `store/` directory to retain device keys and encryption state.

## Community & Policies

- [Code of Conduct](CODE_OF_CONDUCT.md)
- [Contributing](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)
- [Security](docs/security.md)
- [AI Output Disclaimer](docs/ai-output-disclaimer.md)

## License

AGPL‑3.0 — see [LICENSE](LICENSE) for details.
