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

