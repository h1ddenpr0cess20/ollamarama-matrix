# Tools and MCP

This project supports two kinds of tool calling so models can look up information or act on the user’s behalf during a chat:

- Builtin tools bundled with the bot
- External tools exposed by MCP (Model Context Protocol) servers

Both kinds are presented to the model via the Ollama Chat API `tools` schema. The bot automatically merges builtin and MCP tools at startup and lets the model decide when to call them.

## How It Works

When a user chats (`.ai` or `BotName: …`), the bot calls Ollama with a combined tools schema. If the model returns tool calls, the bot executes each call, appends the tool results to the conversation, and asks the model to continue. This loop runs up to 8 iterations.

Key details:

- Tool precedence: if an MCP tool name matches a builtin tool name, the MCP tool takes precedence.
- Logging: tool calls are logged as `Tool (MCP|builtin): <name> args=<json>` with concise, truncated arguments.
- Safety: tool results are coerced to JSON strings before being sent back to the model.

## Builtin Tools

Builtin tools live under `ollamarama/tools/` and are described in a JSON schema file that the bot loads at startup. The schema maps function names to Python callables found in the package.

Schema file:

- `ollamarama/tools/schema.json` — array of tool definitions (OpenAI‑style function schema)

Note: The builtin tools included here are simple examples for demonstration and testing. You can freely add, remove, or replace tools to fit your needs.

Available builtin tools (summary):

| Name | Description |
|------|-------------|
| `get_weather` | Get current weather for a city via Open‑Meteo. |
| `calculate_expression` | Safely evaluate a basic arithmetic expression. |
| `get_time` | Get the current time in UTC, local, or a named timezone. |
| `text_stats` | Return counts of words, characters, and sentences. |
| `fetch_url` | Fetch text content from an HTTP(S) URL with truncation. |

Implementation notes:

- Functions are defined in modules under `ollamarama/tools/` (e.g., `weather.py`, `math.py`, `utils.py`, `text.py`, `web.py`).
- Return values should be JSON‑serializable (dict/list/str/etc.). Non‑serializable values are stringified.
- The schema’s `function.name` must match the Python function name.

### Adding a Builtin Tool

1) Implement a function under `ollamarama/tools/`:

```python
# ollamarama/tools/hello.py
from typing import Dict, Any

def say_hello(name: str = "world") -> Dict[str, Any]:
    return {"greeting": f"Hello, {name}!"}
```

2) Add a tool definition to `ollamarama/tools/schema.json`:

```json
{
  "type": "function",
  "function": {
    "name": "say_hello",
    "description": "Greet a user by name.",
    "parameters": {
      "type": "object",
      "properties": {
        "name": {"type": "string", "description": "Name to greet."}
      },
      "required": [],
      "additionalProperties": false
    }
  }
}
```

No registry changes are needed — the bot discovers the function automatically based on the schema.

## MCP Tools

MCP (Model Context Protocol) lets you run or connect to external tool servers and expose their tools to the model. Ollamarama can connect to one or more MCP servers and merge their tools with builtin tools.

### Configuration

Define MCP servers under `ollama.mcp_servers` in your `config.json`. Each server can be specified in any of these forms:

- URL string: `"http://localhost:9000"`
- Shell string: `"uvx my-mcp-server --port 9000"`
- Arg list: `["uvx", "my-mcp-server", "--port", "9000"]`
- Dict: `{ "command": "uvx", "args": ["my-mcp-server", "--port", "9000"] }`
- Dict with embedded args: `{ "command": "uvx my-mcp-server --port 9000" }`
- Dict URL alias: `{ "url": "http://localhost:9000" }`

Example snippet:

```json
{
  "ollama": {
    "mcp_servers": {
      "notes": "uvx my-notes-mcp --port 8765",
      "browser": { "command": "uvx", "args": ["mcp-browser", "--port", "7777"] },
      "remote": { "url": "http://127.0.0.1:9000" }
    }
  }
}
```

Behavior notes:

- On startup, the bot probes each server, logs how many tools were found, and builds a consolidated client to call tools by name.
- If a server is defined using `command`/`args`, its stderr is silenced to reduce console noise; stdout is preserved for MCP stdio.
- Duplicate names: MCP tools override builtin tools with the same name.

### Verifying MCP Tools

- Start the bot with `-L DEBUG` to see detailed logs.
- Look for lines like `MCP server 'name' returned N tool(s)` and subsequent `Tool (MCP)` call logs when the model uses a tool.

## Troubleshooting

- Model never calls tools: ensure your model supports tool/function calling and that tools appear in logs at startup (or run with `-L DEBUG`).
- HTTP/network errors from tools: check your environment’s network and any proxies/firewalls. MCP servers must be reachable.
- Builtin tool not found: confirm the function name in `schema.json` matches the Python function name and that the module is importable.

## Security Considerations

- Tools (builtin or MCP) can reach external services. Treat outputs as untrusted and avoid exposing sensitive data.
- Limit which MCP servers you enable and prefer local, sandboxed servers where possible.
- Review `docs/security.md` and `SECURITY.md` for broader hardening guidance.
