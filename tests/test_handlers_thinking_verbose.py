from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from ollamarama.handlers.cmd_thinking import handle_thinking
from ollamarama.handlers.cmd_verbose import handle_verbose


def _ctx(**kwargs):
    ctx = SimpleNamespace(
        render=lambda b: b,
        matrix=SimpleNamespace(send_text=AsyncMock()),
        history=SimpleNamespace(set_verbose=lambda v: None),
        log=lambda *a: None,
        **kwargs,
    )
    return ctx


# ---------------------------------------------------------------------------
# .thinking
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_thinking_status_on():
    ctx = _ctx(thinking=True)
    await handle_thinking(ctx, "!r", "@u", "User", "status")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "ON" in body


@pytest.mark.asyncio
async def test_thinking_status_off():
    ctx = _ctx(thinking=False)
    await handle_thinking(ctx, "!r", "@u", "User", "")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_thinking_set_off():
    ctx = _ctx(thinking=True)
    await handle_thinking(ctx, "!r", "@u", "User", "off")
    assert ctx.thinking is False
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_thinking_set_on():
    ctx = _ctx(thinking=False)
    await handle_thinking(ctx, "!r", "@u", "User", "on")
    assert ctx.thinking is True
    body = ctx.matrix.send_text.call_args[0][1]
    assert "ON" in body


@pytest.mark.asyncio
async def test_thinking_toggle():
    ctx = _ctx(thinking=True)
    await handle_thinking(ctx, "!r", "@u", "User", "toggle")
    assert ctx.thinking is False


@pytest.mark.asyncio
async def test_thinking_invalid_arg():
    ctx = _ctx(thinking=True)
    await handle_thinking(ctx, "!r", "@u", "User", "blah")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "Usage" in body
    assert ctx.thinking is True  # unchanged


# ---------------------------------------------------------------------------
# .verbose
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verbose_status_off():
    ctx = _ctx(verbose=False)
    await handle_verbose(ctx, "!r", "@u", "User", "status")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_verbose_status_on():
    ctx = _ctx(verbose=True)
    await handle_verbose(ctx, "!r", "@u", "User", "")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "ON" in body


@pytest.mark.asyncio
async def test_verbose_set_on():
    ctx = _ctx(verbose=False)
    await handle_verbose(ctx, "!r", "@u", "User", "on")
    assert ctx.verbose is True
    body = ctx.matrix.send_text.call_args[0][1]
    assert "ON" in body


@pytest.mark.asyncio
async def test_verbose_set_off():
    ctx = _ctx(verbose=True)
    await handle_verbose(ctx, "!r", "@u", "User", "off")
    assert ctx.verbose is False
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_verbose_toggle():
    ctx = _ctx(verbose=False)
    await handle_verbose(ctx, "!r", "@u", "User", "toggle")
    assert ctx.verbose is True


@pytest.mark.asyncio
async def test_verbose_invalid_arg():
    ctx = _ctx(verbose=False)
    await handle_verbose(ctx, "!r", "@u", "User", "bad")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "Usage" in body
    assert ctx.verbose is False  # unchanged


@pytest.mark.asyncio
async def test_verbose_calls_history_set_verbose():
    called_with = []
    ctx = _ctx(verbose=False)
    ctx.history.set_verbose = lambda v: called_with.append(v)
    await handle_verbose(ctx, "!r", "@u", "User", "on")
    assert called_with == [True]
