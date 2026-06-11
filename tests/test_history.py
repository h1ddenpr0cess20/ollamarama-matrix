import pytest
from ollamarama.history import HistoryStore


def test_history_prompt_and_trim():
    # ~4 chars per token; each message "m{i}" ≈ 2 chars = 0 tokens by integer div.
    # Use longer content so tokens accumulate: 100-char messages ≈ 25 tokens each.
    # Limit to 50 tokens → keep at most ~2 non-system messages.
    hs = HistoryStore("you are ", ".", "helper", max_tokens=50)
    room = "!r:server"
    user = "@u:server"
    # init
    msgs = hs.get(room, user)
    assert msgs[0]["role"] == "system"
    # add messages beyond token budget
    for i in range(10):
        hs.add(room, user, "user", "x" * 100)
    msgs = hs.get(room, user)
    # token budget of 50 means at most a couple messages survive
    total_tokens = sum(len(m.get("content", "")) for m in msgs) // 4
    assert total_tokens <= 50
    # ensure system preserved at index 0 when present
    assert msgs[0]["role"] in ("system", "user")


def test_no_history_clears_after_assistant():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user = "@u:server"

    hs.set_no_history(room, user, True)
    assert hs.get_no_history(room, user) is True

    # Simulate a full exchange
    hs.add(room, user, "user", "Hello")
    # User message should still be present (needed for AI to respond)
    msgs = hs.get(room, user)
    assert any(m["role"] == "user" for m in msgs)

    hs.add(room, user, "assistant", "Hi there!")
    # After assistant response, only system prompt should remain
    msgs = hs.get(room, user)
    assert len(msgs) == 1
    assert msgs[0]["role"] == "system"


def test_no_history_toggle():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user = "@u:server"

    assert hs.get_no_history(room, user) is False
    hs.set_no_history(room, user, True)
    assert hs.get_no_history(room, user) is True
    hs.set_no_history(room, user, False)
    assert hs.get_no_history(room, user) is False


def test_no_history_history_accumulates_normally_when_enabled():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user = "@u:server"

    hs.add(room, user, "user", "msg1")
    hs.add(room, user, "assistant", "resp1")
    hs.add(room, user, "user", "msg2")
    hs.add(room, user, "assistant", "resp2")

    msgs = hs.get(room, user)
    assert len(msgs) == 5  # system + 2 user + 2 assistant


def test_no_history_different_users_isolated():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user_a = "@a:server"
    user_b = "@b:server"

    hs.set_no_history(room, user_a, True)

    hs.add(room, user_a, "user", "Hello")
    hs.add(room, user_a, "assistant", "Hi")
    hs.add(room, user_b, "user", "Hello")
    hs.add(room, user_b, "assistant", "Hi")

    msgs_a = hs.get(room, user_a)
    msgs_b = hs.get(room, user_b)

    # user_a has history off — only system prompt remains
    assert len(msgs_a) == 1 and msgs_a[0]["role"] == "system"
    # user_b has history on — full exchange preserved
    assert len(msgs_b) == 3  # system + user + assistant


def test_global_no_history_toggle():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    assert hs.get_global_no_history() is False
    hs.set_global_no_history(True)
    assert hs.get_global_no_history() is True
    hs.set_global_no_history(False)
    assert hs.get_global_no_history() is False


def test_global_no_history_overrides_per_user():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user = "@u:server"

    # user has history on (default), but global disables it
    hs.set_global_no_history(True)
    hs.add(room, user, "user", "Hello")
    hs.add(room, user, "assistant", "Hi there!")
    msgs = hs.get(room, user)
    assert len(msgs) == 1 and msgs[0]["role"] == "system"


def test_global_no_history_affects_all_users():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user_a = "@a:server"
    user_b = "@b:server"

    hs.set_global_no_history(True)

    for user in (user_a, user_b):
        hs.add(room, user, "user", "Hello")
        hs.add(room, user, "assistant", "Hi")

    for user in (user_a, user_b):
        msgs = hs.get(room, user)
        assert len(msgs) == 1 and msgs[0]["role"] == "system"


def test_global_no_history_get_no_history_returns_true():
    hs = HistoryStore("you are ", ".", "helper", max_tokens=8192)
    room = "!r:server"
    user = "@u:server"

    # Per-user has history enabled, but global flag makes get_no_history True
    assert hs.get_no_history(room, user) is False
    hs.set_global_no_history(True)
    assert hs.get_no_history(room, user) is True


@pytest.mark.asyncio
async def test_handle_history_global_admin_only():
    from unittest.mock import AsyncMock, MagicMock
    from ollamarama.handlers.cmd_history import handle_history

    ctx = MagicMock()
    ctx.admins = ["Admin"]
    ctx.history.get_global_no_history.return_value = False
    ctx.render = lambda b: b
    ctx.matrix.send_text = AsyncMock()

    room = "!r:server"
    sender_id = "@user:server"

    # Non-admin trying global — should be denied
    await handle_history(ctx, room, sender_id, "User", "global on")
    ctx.matrix.send_text.assert_called_once()
    body = ctx.matrix.send_text.call_args[0][1]
    assert "admin" in body.lower()
    ctx.history.set_global_no_history.assert_not_called()


@pytest.mark.asyncio
async def test_handle_history_global_admin_sets():
    from unittest.mock import AsyncMock, MagicMock
    from ollamarama.handlers.cmd_history import handle_history

    ctx = MagicMock()
    ctx.admins = ["Admin"]
    ctx.history.get_global_no_history.return_value = False
    ctx.render = lambda b: b
    ctx.matrix.send_text = AsyncMock()

    room = "!r:server"
    sender_id = "@admin:server"

    # Admin turns global off
    await handle_history(ctx, room, sender_id, "Admin", "global off")
    ctx.history.set_global_no_history.assert_called_once_with(True)
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_handle_history_global_status():
    from unittest.mock import AsyncMock, MagicMock
    from ollamarama.handlers.cmd_history import handle_history

    ctx = MagicMock()
    ctx.admins = ["Admin"]
    ctx.history.get_global_no_history.return_value = True
    ctx.render = lambda b: b
    ctx.matrix.send_text = AsyncMock()

    await handle_history(ctx, "!r:server", "@admin:server", "Admin", "global status")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "OFF" in body


@pytest.mark.asyncio
async def test_handle_history_per_user_shows_global_override_note():
    from unittest.mock import AsyncMock, MagicMock
    from ollamarama.handlers.cmd_history import handle_history

    ctx = MagicMock()
    ctx.admins = []
    # get_no_history returns True (due to global), get_global_no_history True
    ctx.history.get_no_history.return_value = True
    ctx.history.get_global_no_history.return_value = True
    ctx.render = lambda b: b
    ctx.matrix.send_text = AsyncMock()

    await handle_history(ctx, "!r:server", "@u:server", "User", "status")
    body = ctx.matrix.send_text.call_args[0][1]
    assert "global" in body.lower()

