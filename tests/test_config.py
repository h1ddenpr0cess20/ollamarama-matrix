import json
from pathlib import Path

from ollamarama.config import load_config, validate_config


def write_tmp_config(tmp_path: Path) -> Path:
    cfg = {
        "matrix": {
            "server": "https://matrix.org",
            "username": "@bot:matrix.org",
            "password": "x",
            "channels": ["#room:matrix.org"],
            "admins": ["Admin"],
            "device_id": "",
            "store_path": "store",
        },
        "ollama": {
            "api_url": "http://localhost:11434/api/chat",
            "options": {"temperature": 0.8, "top_p": 1, "repeat_penalty": 1},
            "models": {"qwen3": "qwen3"},
            "default_model": "qwen3",
            "prompt": ["you are ", "."],
            "personality": "a helpful assistant",
            "history_tokens": 8192,
            "timeout": 60,
        },
        "markdown": True,
    }
    p = tmp_path / "config.json"
    p.write_text(json.dumps(cfg))
    return p


def test_load_and_validate(tmp_path):
    p = write_tmp_config(tmp_path)
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert ok, errs


def test_timeout_is_read_from_config(tmp_path):
    p = write_tmp_config(tmp_path)
    cfg = load_config(str(p))
    assert cfg.ollama.timeout == 60


def test_timeout_defaults_when_absent(tmp_path):
    p = write_tmp_config(tmp_path)
    data = json.loads(Path(p).read_text())
    del data["ollama"]["timeout"]
    Path(p).write_text(json.dumps(data))
    cfg = load_config(str(p))
    assert cfg.ollama.timeout == 180


def test_invalid_server(tmp_path):
    p = write_tmp_config(tmp_path)
    data = json.loads(Path(p).read_text())
    data["matrix"]["server"] = "not-a-url"
    Path(p).write_text(json.dumps(data))
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert not ok
    assert any("matrix.server" in e for e in errs)

