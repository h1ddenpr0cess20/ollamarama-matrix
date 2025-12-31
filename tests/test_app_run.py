import asyncio
import json
from types import SimpleNamespace

import pytest

import ollamarama.app as appmod
import ollamarama.app_context as app_context
from ollamarama.config import AppConfig, MatrixConfig, OllamaConfig


class FakeMatrixWrapper:
    def __init__(self, server, username, password, device_id, store_path, encryption_enabled=True):
        # mimic underlying client attributes accessed by app
        self.client = SimpleNamespace(device_id="DEV", should_upload_keys=False)
        self.username = username
        self.calls = []
        self.joined = []
        self._to_device = []
        self._text_handlers = []

    async def load_store(self):
        self.calls.append("load_store")

    async def login(self):
        self.calls.append("login")
        return SimpleNamespace(device_id="DEV")

    async def ensure_keys(self):
        self.calls.append("ensure_keys")

    async def initial_sync(self, timeout_ms: int = 3000):
        self.calls.append("initial_sync")

    async def join(self, room_id: str):
        self.joined.append(room_id)

    async def send_text(self, room_id: str, body: str, html=None):
        self.calls.append(("send_text", room_id, body))

    async def display_name(self, user_id: str) -> str:
        return "BotName"

    def add_text_handler(self, handler):
        self._text_handlers.append(handler)

    def add_to_device_callback(self, cb, event_types=None):
        self._to_device.append((cb, event_types))

    async def sync_forever(self, timeout_ms: int = 30000):
        # end immediately so app.run returns
        self.calls.append("sync_forever")


@pytest.mark.asyncio
async def test_app_run_orchestrates_and_persists_device_id(tmp_path, monkeypatch):
    # Patch MatrixClientWrapper used by AppContext to our fake
    monkeypatch.setattr(app_context, "MatrixClientWrapper", FakeMatrixWrapper)

    cfg = AppConfig(
        matrix=MatrixConfig(
            server="https://matrix.org",
            username="@b:matrix.org",
            password="pw",
            channels=["#room:matrix.org"],
            admins=[],
            device_id="",
            store_path=str(tmp_path / "store"),
            e2e=False,
        ),
        ollama=OllamaConfig(
            api_url="http://localhost:11434/api/chat",
            models={"q": "q"},
            default_model="q",
            prompt=["you are ", "."],
            personality="helpful",
            history_size=4,
            timeout=5,
        ),
        markdown=False,
    )
    # Prepare config file for device_id persistence
    cfg_path = tmp_path / "config.json"
    cfg_path.write_text(
        json.dumps(
            {
                "matrix": {
                    "server": cfg.matrix.server,
                    "username": cfg.matrix.username,
                    "password": cfg.matrix.password,
                    "channels": cfg.matrix.channels,
                    "admins": cfg.matrix.admins,
                    "device_id": "",
                    "store_path": cfg.matrix.store_path,
                    "e2e": cfg.matrix.e2e,
                },
                "ollama": {
                    "api_url": cfg.ollama.api_url,
                    "models": cfg.ollama.models,
                    "default_model": cfg.ollama.default_model,
                    "prompt": cfg.ollama.prompt,
                    "personality": cfg.ollama.personality,
                    "history_size": cfg.ollama.history_size,
                    "timeout": cfg.ollama.timeout,
                },
                "markdown": cfg.markdown,
            }
        )
    )

    await appmod.run(cfg, config_path=str(cfg_path))

    # Our fake stores calls on the instance accessible only within run, but we can assert persistence and side effects
    data = json.loads(cfg_path.read_text())
    assert data["matrix"]["device_id"] == "DEV"
