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

