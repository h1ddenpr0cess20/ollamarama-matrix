import asyncio
from types import SimpleNamespace

import pytest

import ollamarama.matrix_client as mc


class FakeAsyncClient:
    def __init__(self, server, username, device_id=None, store_path=None, config=None):
        self.server = server
        self.user = username
        self.device_id = device_id or "D1"
        self.user_id = username
        self.store_path = store_path
        self.config = config
        self.should_upload_keys = True
        self._callbacks = []
        self._to_device_callbacks = []

    async def login(self, password, device_name=None):
        return SimpleNamespace(device_id=self.device_id)

    async def keys_upload(self):
        self.keys_uploaded = True

    def load_store(self):
        # can be sync function
        self.store_loaded = True

    async def join(self, room_id):
        self.joined = getattr(self, "joined", []) + [room_id]

    async def room_send(self, room_id=None, message_type=None, content=None, ignore_unverified_devices=None):
        self.last_send = SimpleNamespace(room_id=room_id, message_type=message_type, content=content)

    async def get_displayname(self, user_id):
        return SimpleNamespace(displayname=f"DN:{user_id}")

    def add_event_callback(self, cb, event_type):
        self._callbacks.append((cb, event_type))

    def add_to_device_callback(self, cb, event_types=None):
        self._to_device_callbacks.append((cb, event_types))

    async def sync(self, timeout=None, full_state=None):
        self.synced = True

    async def sync_forever(self, timeout=None, full_state=None):
        self.sync_loop = True


class FakeAsyncClientConfig:
    def __init__(self, encryption_enabled=True, store_sync_tokens=True):
        self.encryption_enabled = encryption_enabled
        self.store_sync_tokens = store_sync_tokens


@pytest.mark.asyncio
async def test_matrix_client_wrapper_basic(monkeypatch):
    # Patch AsyncClient and config to fakes
    monkeypatch.setattr(mc, "AsyncClient", FakeAsyncClient)
    monkeypatch.setattr(mc, "AsyncClientConfig", FakeAsyncClientConfig)

    w = mc.MatrixClientWrapper(
        server="https://example.org",
        username="@bot:example.org",
        password="pw",
        device_id="",
        store_path="store",
        encryption_enabled=True,
    )

    # login and ensure keys
    await w.login()
    await w.ensure_keys()
    assert getattr(w.client, "keys_uploaded", False) is True

    # load store handles sync function
    await w.load_store()
    assert getattr(w.client, "store_loaded", False) is True

    # join and send
    await w.join("!r")
    await w.send_text("!r", "hello")
    assert w.client.last_send.content["body"] == "hello"

    # html formatting when provided
    await w.send_text("!r", "hello", html="<p>hello</p>")
    content = w.client.last_send.content
    assert content["formatted_body"] == "<p>hello</p>"
    assert content["format"] == "org.matrix.custom.html"

    # display name fallback path
    dn = await w.display_name("@user:example.org")
    assert dn.startswith("DN:@user")

    # event callbacks registration
    seen = {}

    async def handler(room, event):
        seen["ok"] = True

    w.add_text_handler(handler)
    # Trigger stored callback
    cb, _ = w.client._callbacks[-1]
    await cb(SimpleNamespace(room_id="!r"), SimpleNamespace(body="hi", sender="@u", server_timestamp=0))
    assert seen.get("ok") is True

    # to-device callback registration
    w.add_to_device_callback(lambda *a, **k: None, None)
    assert w.client._to_device_callbacks, "to-device callback not registered"

