import json

from cryptography.fernet import Fernet

from ollamarama.history import HistoryStore


def _new_store(tmp_path, key):
    return HistoryStore(
        "you are ",
        ".",
        "helper",
        max_tokens=8192,
        store_path=str(tmp_path),
        encryption_key=key,
    )


def test_persistence_round_trip(tmp_path):
    key = Fernet.generate_key().decode()
    room, user = "!r:server", "@u:server"

    hs = _new_store(tmp_path, key)
    hs.add(room, user, "user", "remember this")
    hs.add(room, user, "assistant", "ok")
    hs.set_no_history(room, user, True)
    hs.set_global_no_history(True)

    hs2 = _new_store(tmp_path, key)
    msgs = hs2.get(room, user)
    assert [m["content"] for m in msgs if m["role"] != "system"] == ["remember this", "ok"]
    assert hs2.get_no_history(room, user) is True
    assert hs2.get_global_no_history() is True


def test_persistence_file_is_encrypted(tmp_path):
    key = Fernet.generate_key().decode()
    hs = _new_store(tmp_path, key)
    hs.add("!r:server", "@u:server", "user", "super secret phrase")

    raw = (tmp_path / "history.enc").read_bytes()
    assert b"super secret phrase" not in raw
    assert b"super secret phrase" in Fernet(key.encode()).decrypt(raw)


def test_wrong_key_starts_empty_without_crashing(tmp_path):
    key = Fernet.generate_key().decode()
    hs = _new_store(tmp_path, key)
    hs.add("!r:server", "@u:server", "user", "data")

    other_key = Fernet.generate_key().decode()
    hs2 = _new_store(tmp_path, other_key)
    assert hs2.get("!r:server", "@u:server")[0]["role"] == "system"
    assert len(hs2.get("!r:server", "@u:server")) == 1


def test_loads_legacy_plain_messages_format(tmp_path):
    key = Fernet.generate_key().decode()
    legacy = {"!r:server": {"@u:server": [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "hi"},
    ]}}
    enc = Fernet(key.encode()).encrypt(json.dumps(legacy).encode())
    (tmp_path / "history.enc").write_bytes(enc)

    hs = _new_store(tmp_path, key)
    msgs = hs.get("!r:server", "@u:server")
    assert msgs[-1] == {"role": "user", "content": "hi"}


def test_no_persistence_without_key(tmp_path):
    hs = HistoryStore("you are ", ".", "helper", store_path=str(tmp_path))
    hs.add("!r:server", "@u:server", "user", "hi")
    assert not (tmp_path / "history.enc").exists()
