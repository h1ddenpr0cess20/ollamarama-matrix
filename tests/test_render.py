import sys
from types import SimpleNamespace

from ollamarama.app import AppContext
import ollamarama.matrix_client as mc
from ollamarama.config import AppConfig, MatrixConfig, OllamaConfig


def make_cfg(markdown=True):
    return AppConfig(
        matrix=MatrixConfig(
            server="https://matrix.org",
            username="@b:matrix.org",
            password="x",
            channels=["#r:matrix.org"],
        ),
        ollama=OllamaConfig(default_model="m", personality="p"),
        markdown=markdown,
    )


def test_render_html_success(monkeypatch):
    class FakeMarkdownMod:
        def markdown(self, text, extensions=None):
            return "<p>" + text + "</p>"

    monkeypatch.setitem(sys.modules, "markdown", FakeMarkdownMod())
    # Patch matrix client deps so AppContext can construct without nio
    class _FakeCfg:
        def __init__(self, **kw):
            pass

    class _FakeClient:
        def __init__(self, *a, **k):
            self.device_id = "D"

    monkeypatch.setattr(mc, "AsyncClientConfig", _FakeCfg)
    monkeypatch.setattr(mc, "AsyncClient", _FakeClient)
    ctx = AppContext(make_cfg())
    html = ctx.render("hello")
    assert html == "<p>hello</p>"


def test_render_disabled_returns_none(monkeypatch):
    # Patch matrix client deps so AppContext can construct without nio
    class _FakeCfg:
        def __init__(self, **kw):
            pass

    class _FakeClient:
        def __init__(self, *a, **k):
            self.device_id = "D"

    monkeypatch.setattr(mc, "AsyncClientConfig", _FakeCfg)
    monkeypatch.setattr(mc, "AsyncClient", _FakeClient)
    ctx = AppContext(make_cfg(markdown=False))
    assert ctx.render("hello") is None
