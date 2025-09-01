from types import SimpleNamespace

from ollamarama.ollama_client import OllamaClient


class DummyResp:
    def __init__(self, status=200, data=None):
        self.status_code = status
        self._data = data or {"message": {"content": "ok"}}
        self.ok = True

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception("bad status")

    def json(self):
        return self._data


class DummySession:
    def __init__(self):
        self.last = None

    def post(self, url, json=None, timeout=None):
        self.last = SimpleNamespace(url=url, json=json, timeout=timeout)
        return DummyResp(200, {"message": {"content": "hello"}})

    def get(self, url, timeout=None):
        return DummyResp(200, {})

    def head(self, url, timeout=None):
        return DummyResp(200, {})


def test_chat_builds_payload():
    s = DummySession()
    c = OllamaClient(base_url="http://x/api", timeout=10, session=s)
    data = c.chat(messages=[{"role": "user", "content": "hi"}], model="m", options={"temperature": 1}, timeout=5)
    assert data["message"]["content"] == "hello"
    assert s.last.url.endswith("/chat")
    assert s.last.json["model"] == "m"
    assert s.last.json["messages"][0]["content"] == "hi"
    assert s.last.json["options"]["temperature"] == 1


def test_health():
    s = DummySession()
    c = OllamaClient(base_url="http://x/api", session=s)
    assert c.health() is True

