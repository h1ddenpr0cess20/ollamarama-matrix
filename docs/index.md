# Ollamarama Matrix Bot

Ollamarama is a Matrix chatbot powered by local LLMs via the Ollama Chat API. It brings fast, private AI assistance to your Matrix rooms with per‑user history, switchable models, and dynamic personalities.

- Source: <https://github.com/h1ddenpr0cess20/ollamarama-matrix>
- License: AGPL‑3.0

## Highlights

- Dynamic personalities and custom prompts per user
- Per‑room and per‑user conversation histories
- Admin model switching and global resets
- Optional Markdown rendering for rich replies
- Secure by default: no secrets in repo, E2E‑ready with matrix‑nio

## Quick Links

- [Getting Started](getting-started.md)
- [Ollama Setup](ollama.md)
- [Configuration](configuration.md)
- [Commands](commands.md)
- [Tools & MCP](tools-and-mcp.md)
- [Docker](docker.md)
- [Architecture](architecture.md)
- [CLI Reference](cli.md)
- [Operations & Security](operations.md)
- [Not a Companion — Please Read](not-a-companion.md)
- [Development Guide](development.md)
- [Migration Notes](migration.md)
- [Refactor Blueprint (historic)](refactor-plan.md)
- [Legacy → New Map](legacy-map.md)

## Overview

Ollamarama connects a Matrix client (matrix‑nio) to the Ollama Chat API. Incoming room messages are routed to command handlers (e.g., `.ai`, `.model`, `.persona`). Each user in each room has an independent chat history seeded with a system prompt (personality). Handlers compose a message list, call Ollama for a reply, and send a Markdown‑rendered response back to the room. Admins can switch the active model or reset global state.

## Supported Environments

- Python 3.8+
- Ollama running locally or reachable on your network
- Optional E2E encryption via `matrix-nio[e2e]` (requires libolm)

## Support & Issues

Please open GitHub issues with clear repro steps and relevant logs (redact credentials). Pull requests are welcome; see [Development Guide](development.md) for coding and testing guidelines.
