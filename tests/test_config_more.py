import json
from pathlib import Path

import pytest

from ollamarama.config import load_config, validate_config


def write_cfg(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "config.json"
    p.write_text(json.dumps(data))
    return p


def base_cfg() -> dict:
    return {
        "matrix": {
            "server": "https://matrix.org",
            "username": "@bot:matrix.org",
            "password": "x",
            "channels": ["#room:matrix.org"],
            "admins": ["Admin"],
            "store_path": "store",
        },
        "ollama": {
            "api_url": "http://localhost:11434/api/chat",
            "options": {"temperature": 0.8, "top_p": 1, "repeat_penalty": 1},
            "models": {"qwen3": "qwen3"},
            "default_model": "qwen3",
            "prompt": ["you are ", "."],
            "personality": "a helpful assistant",
            "history_size": 24,
            "timeout": 60,
        },
        "markdown": True,
    }


def test_validate_bounds_and_default_model(tmp_path):
    data = base_cfg()
    # Invalid bounds
    data["ollama"]["options"]["temperature"] = 3
    p = write_cfg(tmp_path, data)
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert not ok
    assert any("temperature" in e for e in errs)

    # Default model not in mapping
    data = base_cfg()
    data["ollama"]["default_model"] = "missing"
    p = write_cfg(tmp_path, data)
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert not ok
    assert any("default_model" in e for e in errs)


def test_validate_prompt_shape(tmp_path):
    data = base_cfg()
    data["ollama"]["prompt"] = ["only-one"]
    p = write_cfg(tmp_path, data)
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert not ok
    assert any("prompt" in e for e in errs)


def test_env_overrides(tmp_path, monkeypatch):
    data = base_cfg()
    p = write_cfg(tmp_path, data)
    monkeypatch.setenv("OLLAMARAMA_OLLAMA_URL", "http://host:1234/api/chat")
    monkeypatch.setenv("OLLAMARAMA_MODEL", "qwen3")
    monkeypatch.setenv("OLLAMARAMA_STORE_PATH", "st")
    monkeypatch.setenv("OLLAMARAMA_MATRIX_SERVER", "https://example.org")
    cfg = load_config(str(p))
    assert cfg.ollama.api_url == "http://host:1234/api/chat"
    assert cfg.matrix.store_path == "st"
    assert cfg.matrix.server == "https://example.org"

