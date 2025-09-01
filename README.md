# ollamarama-matrix

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Matrix Protocol](https://img.shields.io/badge/chat-Matrix-green.svg)](https://matrix.org/)
[![Ollama](https://img.shields.io/badge/AI-Ollama-orange.svg)](https://ollama.com/)

Ollamarama is a Matrix chatbot powered by local LLMs via the Ollama Chat API. It brings private, fast AI assistance to your rooms with per‑user history, dynamic personalities, and admin‑level model control.

Docs quick links:

- Getting Started: `docs/getting-started.md`
- Configuration: `docs/configuration.md`
- Commands: `docs/commands.md`
- CLI Reference: `docs/cli.md`
- Architecture: `docs/architecture.md`
- Operations: `docs/operations.md`
- Development: `docs/development.md`
- Migration & Legacy Map: `docs/migration.md`, `docs/legacy-map.md`
- Security & Disclaimer: `docs/security.md`, `docs/ai-output-disclaimer.md`

## Features

- Dynamic personalities with quick switching
- Per‑user history, isolated per room and user
- Collaborative mode to talk across histories
- Admin controls for model switching and resets
- Custom system prompts for specialized tasks

## Quick Start

1) Install Ollama and pull a model

```bash
curl https://ollama.com/install.sh | sh
ollama pull qwen3
```

2) Install Python deps

```bash
pip install -r requirements.txt
```

3) Configure and run

Edit `config.json` with your Matrix server, bot account, and room(s), then run:

```bash
ollamarama-matrix --config config.json
```

Full setup details: see `docs/getting-started.md` and `docs/configuration.md`.

## Usage

Common commands (full list in `docs/commands.md`):

- `.ai <message>` or `botname: <message>`: chat with the AI
- `.x <user> <message>`: talk using another user’s context
- `.persona <name>`: change the AI personality
- `.custom <prompt>`: use a custom system prompt
- `.reset` / `.stock`: clear history (with or without system prompt)
- Admin: `.model [name]` to show/change model; `.clear` reset for all

## Encryption Support

- Works in encrypted Matrix rooms using `matrix-nio[e2e]` with device verification.
- Requires `libolm` available to Python for E2E. On Windows, build/install `libolm` or use WSL if needed.
- Include a `store` path in `config.json` to persist encryption state and device IDs.

## Community & Policies

- Code of Conduct: `CODE_OF_CONDUCT.md`
- Contributing: `CONTRIBUTING.md`
- Security Policy and Hardening: `SECURITY.md`, `docs/security.md`
- AI Output Disclaimer: `docs/ai-output-disclaimer.md`

## License

AGPL‑3.0 — see `LICENSE` for details.
