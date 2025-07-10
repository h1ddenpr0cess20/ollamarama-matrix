# ollamarama-matrix

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Matrix Protocol](https://img.shields.io/badge/chat-Matrix-green.svg)](https://matrix.org/)
[![Ollama](https://img.shields.io/badge/AI-Ollama-orange.svg)](https://ollama.com/)
[![GitHub](https://img.shields.io/github/stars/h1ddenpr0cess20/ollamarama-matrix?style=social)](https://github.com/h1ddenpr0cess20/ollamarama-matrix)

Ollamarama is a powerful AI chatbot for the [Matrix](https://matrix.org/) chat protocol powered by [Ollama](https://ollama.com/). Transform your Matrix channels with an AI that can roleplay as virtually anything you can imagine.

## ✨ Features

- 🎭 **Dynamic Personalities**: Switch between different AI personalities on the fly
- 👥 **Per-User Chat History**: Each user maintains their own conversation context
- 🔒 **Channel Isolation**: Conversations are separated by channel and user
- 🤝 **Collaborative Mode**: Users can interact with each other's chat histories
- 🛠️ **Admin Controls**: Model switching and global reset capabilities
- 🎯 **Custom Prompts**: Use your own system prompts for specialized interactions

## 🌟 Related Projects

- 💬 **IRC Version**: [ollamarama-irc](https://github.com/h1ddenpr0cess20/ollamarama-irc)
- 🖥️ **Terminal Version**: [ollamarama](https://github.com/h1ddenpr0cess20/ollamarama)

## 🚀 Quick Start

### Prerequisites

Install and familiarize yourself with [Ollama](https://ollama.com/) to run local LLMs.

```bash
curl https://ollama.com/install.sh | sh
```

### 1. Install AI Models

Download the models you want to use from the [Ollama library](https://ollama.com/library).

**🎯 Recommended model:**
```bash
ollama pull qwen3
```


### 2. Install Dependencies

```bash
pip install -r requirements.txt
```
This installs `matrix-nio` with encryption support so the bot can work in encrypted rooms.

### 3. Configure Matrix Bot

1. Set up a [Matrix account](https://app.element.io/) for your bot
2. Get your server URL, username, and password
3. Update the `config.json` file with your credentials:

```json
{
    "matrix": {
        "server": "https://matrix.org",
        "username": "@your_bot:matrix.org",
        "password": "your_password",
        "channels": ["#your-channel:matrix.org"],
        "store_path": "store"
    }
}
```

### 4. Run the Bot

```bash
python ollamarama.py
```

## 📖 Usage Guide

### Basic Commands

| Command | Description | Example |
|---------|-------------|---------|
| `.ai <message>` or `botname: <message>` | Basic chat with the AI | `.ai Hello there!` |
| `.x <user> <message>` | Talk to another user's chat history | `.x Alice What did we discuss?` |
| `.persona <personality>` | Change AI personality | `.persona helpful librarian` |
| `.custom <prompt>` | Use custom system prompt | `.custom You are a coding expert` |
| `.reset` | Clear history, reset to default personality | `.reset` |
| `.stock` | Clear history, use without system prompt | `.stock` |

### 👑 Admin Commands

| Command | Description | Example |
|---------|-------------|---------|
| `.model [model_name]` | Show/change current model | `.model qwen3` |
| `.clear` | Reset bot for all users | `.clear` |

### 💡 Pro Tips

- **Personality Examples**: Try `detective`, `pirate`, `shakespeare`, `helpful assistant`, `sarcastic critic`
- **Collaborative Mode**: Use `.x username` to continue someone else's conversation
- **Custom Prompts**: Perfect for specialized tasks like code review or creative writing

## Encryption Support

- This bot supports end-to-end encryption (E2E) in Matrix rooms using `matrix-nio[e2e]` and a built-in device verification system.
- You must have `libolm` installed and available to Python for E2E to work.
- On Windows, you need to build and install `libolm` from source for encryption support. If you do not need encrypted rooms or have issues with `libolm`, use the files in the `no-e2e/` folder, or run it using Windows Subsystem for Linux (WSL).

## ⚖️ License

This project is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. See the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Feel free to:
- 🐛 Report bugs
- 💡 Suggest features
- 🔧 Submit pull requests

## ⭐ Show Your Support

If you find this project useful, please consider giving it a star on GitHub!


