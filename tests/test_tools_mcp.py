import json
from types import SimpleNamespace

import pytest

from ollamarama.fastmcp_client import FastMCPClient
from ollamarama.handlers.cmd_ai import handle_ai
from ollamarama.history import HistoryStore
from ollamarama.tools import load_schema
from ollamarama.app import AppContext


class FakeTool:
    def __init__(self):
        self.name = "echo"
        self.description = "Echo text"
        self.inputSchema = {"type": "object", "properties": {"text": {"type": "string"}}}


class FakeMCPClient:
    def __init__(self, cfg):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def list_tools(self):
        return [FakeTool()]

    async def call_tool(self, name, arguments):
        class Res:
            def __init__(self, data):
                self.data = data
                self.structured_content = None
                self.content = []
        return Res({"echo": arguments.get("text", "")})


def fake_client(cfg):
    return FakeMCPClient(cfg)


def test_fastmcp_client(monkeypatch):
    monkeypatch.setattr("ollamarama.fastmcp_client.Client", fake_client)
    client = FastMCPClient({"s": {"command": "none"}})
    tools = client.list_tools()
    assert tools[0]["function"]["name"] == "echo"
    data = json.loads(client.call_tool("echo", {"text": "hi"}))
    assert data["echo"] == "hi"


class FakeOllama:
    def __init__(self):
        self.calls = 0

    def chat_with_tools(self, model, messages, options, tools, tool_choice=None, timeout=None):
        if self.calls == 0:
            self.calls += 1
            return {
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "1",
                            "type": "function",
                            "function": {
                                "name": "calculate_expression",
                                "arguments": json.dumps({"expression": "2+2"}),
                            },
                        }
                    ],
                }
            }
        return {"message": {"role": "assistant", "content": "4"}}


class FakeMatrix:
    def __init__(self):
        self.sent = []

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))


async def _to_thread(fn, *a, **kw):
    return fn(*a, **kw)


@pytest.mark.asyncio
async def test_handle_ai_with_tools():
    schema = load_schema()
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=FakeMatrix(),
        ollama=FakeOllama(),
        to_thread=_to_thread,
        render=lambda s: None,
        model="qwen3",
        options={},
        timeout=10,
        log=lambda *a, **k: None,
        tools_enabled=True,
        tools_schema=schema,
        _mcp_tool_names=set(),
        mcp_client=None,
    )
    ctx.respond_with_tools = AppContext.respond_with_tools.__get__(ctx)
    ctx._execute_tool = AppContext._execute_tool.__get__(ctx)
    await handle_ai(ctx, "!r", "@u", "User", "what is 2+2")
    sent_body = ctx.matrix.sent[-1][1]
    assert "4" in sent_body
