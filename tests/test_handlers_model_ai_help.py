import asyncio
from types import SimpleNamespace

import pytest

from ollamarama.handlers.cmd_model import handle_model
from ollamarama.handlers.cmd_ai import handle_ai
from ollamarama.handlers.cmd_help import handle_help
from ollamarama.history import HistoryStore


class FakeMatrix:
    def __init__(self):
        self.sent = []

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))


class FakeOllama:
    def __init__(self, response_text):
        self.response_text = response_text

    def chat(self, messages, model, options=None, timeout=None):
        return {"message": {"content": self.response_text}}


async def _to_thread(fn, *a, **kw):
    return fn(*a, **kw)


@pytest.mark.asyncio
async def test_handle_model_show_and_set_and_reset():
    ctx = SimpleNamespace(
        model="qwen3",
        default_model="qwen3",
        models={"qwen": "qwen3", "llama": "llama3"},
        render=lambda s: None,
        matrix=FakeMatrix(),
        log=lambda *a, **k: None,
    )
    # No args → show current and available
    await handle_model(ctx, "!r", "@u", "Admin", "")
    assert "Current model" in ctx.matrix.sent[-1][1]
    assert "Available models" in ctx.matrix.sent[-1][1]
    # Set by key
    await handle_model(ctx, "!r", "@u", "Admin", "qwen")
    assert ctx.model == "qwen3"
    # Reset
    await handle_model(ctx, "!r", "@u", "Admin", "reset")
    assert ctx.model == ctx.default_model


@pytest.mark.asyncio
async def test_handle_ai_strips_thinking_markers():
    # Include all supported markers in a single response
    content = (
        "<think>plan</think> Hello <|begin_of_thought|>inner<|end_of_thought|>"
        " <|begin_of_solution|>final answer<|end_of_solution|>"
    )
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=FakeMatrix(),
        ollama=FakeOllama(content),
        to_thread=_to_thread,
        render=lambda s: None,
        model="qwen3",
        options={},
        timeout=10,
        log=lambda *a, **k: None,
    )
    await handle_ai(ctx, "!r", "@u", "User", "hello")
    # Ensure the sent body does not contain think/thought markers
    sent_body = ctx.matrix.sent[-1][1]
    assert "<think>" not in sent_body and "<|begin_of_thought|>" not in sent_body
    assert "final answer" in sent_body or "Hello" in sent_body


@pytest.mark.asyncio
async def test_handle_ai_trims_whitespace_simple():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=FakeMatrix(),
        ollama=FakeOllama("   hello world  \n\n"),
        to_thread=_to_thread,
        render=lambda s: None,
        model="qwen3",
        options={},
        timeout=10,
        log=lambda *a, **k: None,
    )
    await handle_ai(ctx, "!r", "@u", "User", "hi")
    sent_body = ctx.matrix.sent[-1][1]
    assert sent_body.endswith("hello world")
    assert not sent_body.rstrip().endswith(" ")


@pytest.mark.asyncio
async def test_handle_help_splits_admin_section():
    ctx = SimpleNamespace(
        matrix=FakeMatrix(),
        admins=["Admin"],
        render=lambda s: None,
    )
    # Non‑admin sees only first section
    await handle_help(ctx, "!r", "@u", "User", "")
    assert len(ctx.matrix.sent) == 1
    # Admin sees both sections when separator is present
    ctx.matrix.sent.clear()
    await handle_help(ctx, "!r", "@u", "Admin", "")
    assert len(ctx.matrix.sent) >= 1
    # If repo help.txt has the admin section, there should be 2 messages
    if "~~~" in open("help.md").read():
        assert len(ctx.matrix.sent) == 2
