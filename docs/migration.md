# Migration Notes

The project moved from a single‑file script to a modular package. The new CLI runs the modern implementation and supports a config validation dry‑run. The legacy code remains under `legacy/` for historical reference only.

## What Changed

- Installed command is `ollamarama-matrix`; module entry `python -m ollamarama` remains available
- Clear separation of concerns: config, Matrix wrapper, handlers, history, Ollama client
- Tests and documentation are first‑class

## How To Run (now)

- Start the bot: `ollamarama-matrix --config config.json`
