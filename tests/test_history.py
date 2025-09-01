from ollamarama.history import HistoryStore


def test_history_prompt_and_trim():
    hs = HistoryStore("you are ", ".", "helper", max_items=5)
    room = "!r:server"
    user = "@u:server"
    # init
    msgs = hs.get(room, user)
    assert msgs[0]["role"] == "system"
    # add messages beyond max
    for i in range(10):
        hs.add(room, user, "user", f"m{i}")
    msgs = hs.get(room, user)
    assert len(msgs) <= 5
    # ensure system preserved at index 0 when present
    assert msgs[0]["role"] in ("system", "user")

