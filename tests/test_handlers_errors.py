import asyncio
from types import SimpleNamespace

import pytest

from ollamarama.handlers.cmd_ai import handle_ai
from ollamarama.handlers.cmd_x import handle_x
from ollamarama.history import HistoryStore


class FakeMatrix:
    def __init__(self):
        self.sent = []

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))

    async def display_name(self, user_id: str) -> str:
        return user_id


class FailingOllama:
    def chat(self, *a, **k):
        raise RuntimeError("boom")


async def _to_thread(fn, *a, **kw):
    # Simulate asyncio.to_thread by directly executing
    return fn(*a, **kw)


@pytest.mark.asyncio
async def test_handle_ai_error_path_sends_message():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=4),
        matrix=FakeMatrix(),
        ollama=FailingOllama(),
        to_thread=_to_thread,
        render=lambda s: None,
        model="m",
        options={},
        timeout=5,
        log=lambda *a, **k: None,
    )
    await handle_ai(ctx, "!r", "@u", "User", "hello")
    assert ctx.matrix.sent, "should send error message"
    assert "Something went wrong" in ctx.matrix.sent[-1][1]


@pytest.mark.asyncio
async def test_handle_x_error_path_sends_message():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=4),
        matrix=FakeMatrix(),
        ollama=FailingOllama(),
        to_thread=_to_thread,
        render=lambda s: None,
        model="m",
        options={},
        timeout=5,
        log=lambda *a, **k: None,
    )
    # Seed a target with history so handler proceeds
    ctx.history.add("!r", "@t", "user", "hi")
    await handle_x(ctx, "!r", "@s", "Sender", "@t hello")
    assert ctx.matrix.sent, "should send error message"
    assert "Something went wrong" in ctx.matrix.sent[-1][1]

