from types import SimpleNamespace

import pytest
import requests

from ollamarama.exceptions import NetworkError, RuntimeFailure
from ollamarama.ollama_client import OllamaClient


class Resp:
    def __init__(self, *, data=None, raise_json=False, ok=True, status=200):
        self._data = data
        self._raise_json = raise_json
        self.ok = ok
        self.status_code = status

    def raise_for_status(self):
        if not self.ok:
            raise requests.HTTPError("bad status")

    def json(self):
        if self._raise_json:
            raise ValueError("not json")
        return self._data


def test_chat_raises_network_error_on_request_exception():
    class S:
        def post(self, *a, **k):
            raise requests.ConnectionError("refused")

    c = OllamaClient(base_url="http://x/api", session=S())
    with pytest.raises(NetworkError):
        c.chat(messages=[], model="m")


def test_chat_raises_runtime_failure_on_bad_json():
    class S:
        def post(self, *a, **k):
            return Resp(raise_json=True)

    c = OllamaClient(base_url="http://x/api", session=S())
    with pytest.raises(RuntimeFailure):
        c.chat(messages=[], model="m")


def test_chat_with_tools_builds_payload_and_parses():
    captured = {}

    class S:
        def post(self, url, json=None, timeout=None):
            captured["url"] = url
            captured["json"] = json
            return Resp(data={"message": {"content": "done"}})

    c = OllamaClient(base_url="http://x/api", session=S())
    out = c.chat_with_tools(
        messages=[{"role": "user", "content": "hi"}],
        model="m",
        options={"temperature": 0.5},
        tools=[{"type": "function"}],
        tool_choice="auto",
        timeout=7,
    )
    assert out["message"]["content"] == "done"
    assert captured["url"].endswith("/chat")
    assert captured["json"]["tools"] == [{"type": "function"}]
    assert captured["json"]["tool_choice"] == "auto"
    assert captured["json"]["options"] == {"temperature": 0.5}
    assert captured["json"]["stream"] is False


def test_list_models_success():
    class S:
        def get(self, url, timeout=None):
            return Resp(data={"models": [{"name": "qwen3"}, {"model": "llama3"}]})

    c = OllamaClient(base_url="http://x/api", session=S())
    assert c.list_models() == {"qwen3": "qwen3", "llama3": "llama3"}


def test_list_models_empty_raises():
    class S:
        def get(self, url, timeout=None):
            return Resp(data={"models": []})

    c = OllamaClient(base_url="http://x/api", session=S())
    with pytest.raises(RuntimeFailure):
        c.list_models()


def test_list_models_network_error():
    class S:
        def get(self, url, timeout=None):
            raise requests.ConnectionError("down")

    c = OllamaClient(base_url="http://x/api", session=S())
    with pytest.raises(NetworkError):
        c.list_models()


def test_health_falls_back_to_head():
    class S:
        def get(self, url, timeout=None):
            raise requests.ConnectionError("no /tags")

        def head(self, url, timeout=None):
            return SimpleNamespace(ok=True)

    c = OllamaClient(base_url="http://x/api", session=S())
    assert c.health() is True


def test_health_false_when_everything_fails():
    class S:
        def get(self, url, timeout=None):
            raise requests.ConnectionError("x")

        def head(self, url, timeout=None):
            raise requests.ConnectionError("x")

    c = OllamaClient(base_url="http://x/api", session=S())
    assert c.health() is False
