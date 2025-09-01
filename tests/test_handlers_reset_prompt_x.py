import asyncio
from types import SimpleNamespace

import pytest

from ollamarama.handlers.cmd_reset import handle_reset, handle_clear
from ollamarama.handlers.cmd_prompt import handle_persona, handle_custom
from ollamarama.handlers.cmd_x import handle_x
from ollamarama.history import HistoryStore


class FakeMatrix:
    def __init__(self, names=None):
        self.sent = []
        self._names = names or {}

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body, html))

    async def display_name(self, user_id: str) -> str:
        return self._names.get(user_id, user_id)


class FakeOllama:
    def __init__(self, response_text="ok"):
        self.response_text = response_text

    def chat(self, messages, model, options=None, timeout=None):
        return {"message": {"content": self.response_text}}


async def _to_thread(fn, *a, **kw):
    return fn(*a, **kw)


@pytest.mark.asyncio
async def test_handle_reset_stock_and_default():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=4),
        matrix=FakeMatrix(),
        default_model="qwen3",
        default_personality="helper",
        bot_id="Bot",
        render=lambda s: None,
        log=lambda *a, **k: None,
    )
    room = "!r"
    user = "@u"
    name = "User"
    # non-stock
    await handle_reset(ctx, room, user, name, "")
    assert any("reset to default" in body for _, body, _ in ctx.matrix.sent)
    # stock
    ctx.matrix.sent.clear()
    await handle_reset(ctx, room, user, name, "stock")
    assert any("Stock settings" in body for _, body, _ in ctx.matrix.sent)


@pytest.mark.asyncio
async def test_handle_clear_global_reset():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=4),
        matrix=FakeMatrix(),
        default_model="m0",
        default_personality="p0",
        model="m1",
        personality="p1",
        render=lambda s: None,
        log=lambda *a, **k: None,
    )
    await handle_clear(ctx, "!r", "@u", "Admin", "")
    assert ctx.model == ctx.default_model
    assert ctx.personality == ctx.default_personality
    assert any("reset for everyone" in body for _, body, _ in ctx.matrix.sent)


@pytest.mark.asyncio
async def test_handle_persona_and_custom():
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=FakeMatrix(),
        ollama=FakeOllama("hello there"),
        to_thread=_to_thread,
        model="qwen3",
        options={},
        timeout=10,
        render=lambda s: None,
        log=lambda *a, **k: None,
    )
    room = "!r"
    user = "@u"
    await handle_persona(ctx, room, user, "User", "detective")
    msgs = ctx.history.get(room, user)
    assert msgs[0]["role"] == "system" and "detective" in msgs[0]["content"]
    # custom overrides persona format
    await handle_custom(ctx, room, user, "User", "You are strict.")
    msgs = ctx.history.get(room, user)
    assert msgs[0]["content"].startswith("You are strict.")


@pytest.mark.asyncio
async def test_handle_x_resolves_display_name_and_replies():
    room = "!r"
    sender = "@s"
    target = "@t"
    names = {sender: "Alice", target: "Bob"}
    matrix = FakeMatrix(names=names)
    ctx = SimpleNamespace(
        history=HistoryStore("you are ", ".", "helper", max_items=8),
        matrix=matrix,
        ollama=FakeOllama("ok"),
        to_thread=_to_thread,
        model="qwen3",
        options={},
        timeout=10,
        render=lambda s: None,
        log=lambda *a, **k: None,
    )
    # Seed history for target so handler proceeds
    ctx.history.add(room, target, "user", "hi")
    await handle_x(ctx, room, sender, names[sender], f"{names[target]} what up")
    assert matrix.sent, "should send a reply to room"
    body = matrix.sent[-1][1]
    assert body.startswith("**Alice**:\n")

