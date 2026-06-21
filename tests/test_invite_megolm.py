from types import SimpleNamespace

import pytest

from ollamarama.app_runtime import _make_invite_handler, _make_undecrypted_handler
from ollamarama.config import AppConfig, MatrixConfig, OllamaConfig


class FakeMatrix:
    def __init__(self):
        self.joined = []
        self.left = []
        self.sent = []
        self.key_requests = []

    async def join(self, room_id):
        self.joined.append(room_id)

    async def leave(self, room_id):
        self.left.append(room_id)

    async def send_text(self, room_id, body, html=None):
        self.sent.append((room_id, body))

    async def request_room_key(self, event):
        self.key_requests.append(event)

    async def display_name(self, user_id):
        return f"DN:{user_id}"


def _ctx(matrix):
    return SimpleNamespace(matrix=matrix, render=lambda b: None, log=lambda *a, **k: None)


def _cfg():
    return AppConfig(
        matrix=MatrixConfig(
            server="https://m.org", username="@bot:m.org", password="x",
            channels=["#r:m.org"],
        ),
        ollama=OllamaConfig(default_model="q", personality="helper"),
    )


@pytest.mark.asyncio
async def test_invite_joins_replies_and_leaves():
    matrix = FakeMatrix()
    cfg = _cfg()
    handler = _make_invite_handler(_ctx(matrix), cfg)

    room = SimpleNamespace(room_id="!new:m.org")
    event = SimpleNamespace(state_key="@bot:m.org", membership="invite", sender="@rude:m.org")
    await handler(room, event)

    assert matrix.joined == ["!new:m.org"]
    assert matrix.left == ["!new:m.org"]
    assert len(matrix.sent) == 1
    body = matrix.sent[0][1]
    assert "DN:@rude:m.org" in body  # inviter name interpolated into {name}


@pytest.mark.asyncio
async def test_invite_ignores_other_members_invites():
    matrix = FakeMatrix()
    handler = _make_invite_handler(_ctx(matrix), _cfg())

    room = SimpleNamespace(room_id="!new:m.org")
    # Invite is for a different user, not the bot
    event = SimpleNamespace(state_key="@someone:m.org", membership="invite", sender="@x:m.org")
    await handler(room, event)

    assert matrix.joined == [] and matrix.left == [] and matrix.sent == []


@pytest.mark.asyncio
async def test_invite_still_leaves_when_send_fails():
    class Boom(FakeMatrix):
        async def send_text(self, room_id, body, html=None):
            raise RuntimeError("send failed")

    matrix = Boom()
    handler = _make_invite_handler(_ctx(matrix), _cfg())
    room = SimpleNamespace(room_id="!new:m.org")
    event = SimpleNamespace(state_key="@bot:m.org", membership="invite", sender="@r:m.org")
    await handler(room, event)

    # The finally clause must still leave the room even if the message fails
    assert matrix.left == ["!new:m.org"]


@pytest.mark.asyncio
async def test_custom_invite_reply_is_used():
    matrix = FakeMatrix()
    cfg = _cfg()
    cfg.matrix.invite_reply = "go away {name}"
    handler = _make_invite_handler(_ctx(matrix), cfg)
    room = SimpleNamespace(room_id="!n:m.org")
    event = SimpleNamespace(state_key="@bot:m.org", membership="invite", sender="@p:m.org")
    await handler(room, event)
    assert matrix.sent[0][1] == "go away DN:@p:m.org"


@pytest.mark.asyncio
async def test_undecrypted_requests_room_key():
    matrix = FakeMatrix()
    handler = _make_undecrypted_handler(_ctx(matrix))
    room = SimpleNamespace(room_id="!enc:m.org")
    event = SimpleNamespace(session_id="sess1")
    await handler(room, event)
    assert matrix.key_requests == [event]
