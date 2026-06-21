from unittest.mock import AsyncMock, MagicMock

import pytest

from ollamarama.handlers.cmd_history import handle_history


def _ctx(*, admins=None, global_off=False, user_off=False):
    ctx = MagicMock()
    ctx.admins = admins or []
    ctx.render = lambda b: b
    ctx.matrix.send_text = AsyncMock()
    ctx.history.get_global_no_history.return_value = global_off
    ctx.history.get_no_history.return_value = global_off or user_off
    return ctx


def _last_body(ctx):
    return ctx.matrix.send_text.call_args[0][1]


# -- per-user toggle -----------------------------------------------------------

@pytest.mark.asyncio
async def test_per_user_off():
    ctx = _ctx()
    await handle_history(ctx, "!r", "@u", "User", "off")
    ctx.history.set_no_history.assert_called_once_with("!r", "@u", True)
    assert "OFF" in _last_body(ctx)


@pytest.mark.asyncio
async def test_per_user_on():
    ctx = _ctx(user_off=True)
    await handle_history(ctx, "!r", "@u", "User", "on")
    ctx.history.set_no_history.assert_called_once_with("!r", "@u", False)
    assert "ON" in _last_body(ctx)


@pytest.mark.asyncio
async def test_per_user_toggle_flips_current_state():
    ctx = _ctx(user_off=True)  # currently disabled → toggle should enable
    await handle_history(ctx, "!r", "@u", "User", "toggle")
    ctx.history.set_no_history.assert_called_once_with("!r", "@u", False)


@pytest.mark.asyncio
async def test_per_user_status_default_on():
    ctx = _ctx()
    await handle_history(ctx, "!r", "@u", "User", "")
    ctx.history.set_no_history.assert_not_called()
    assert "ON" in _last_body(ctx)


@pytest.mark.asyncio
async def test_per_user_invalid_arg_shows_usage():
    ctx = _ctx()
    await handle_history(ctx, "!r", "@u", "User", "maybe")
    ctx.history.set_no_history.assert_not_called()
    assert "Usage" in _last_body(ctx)


@pytest.mark.asyncio
async def test_per_user_on_warns_when_global_override_active():
    ctx = _ctx(global_off=True)
    await handle_history(ctx, "!r", "@u", "User", "on")
    assert "global override is ON" in _last_body(ctx)


# -- global toggle (admin) -----------------------------------------------------

@pytest.mark.asyncio
async def test_global_toggle_flips_state():
    ctx = _ctx(admins=["Admin"], global_off=False)
    await handle_history(ctx, "!r", "@a", "Admin", "global toggle")
    ctx.history.set_global_no_history.assert_called_once_with(True)


@pytest.mark.asyncio
async def test_global_invalid_subcommand_shows_usage():
    ctx = _ctx(admins=["Admin"])
    await handle_history(ctx, "!r", "@a", "Admin", "global wat")
    ctx.history.set_global_no_history.assert_not_called()
    assert "Usage" in _last_body(ctx)
