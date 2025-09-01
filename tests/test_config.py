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
            "history_size": 24,
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


def test_invalid_server(tmp_path):
    p = write_tmp_config(tmp_path)
    data = json.loads(Path(p).read_text())
    data["matrix"]["server"] = "not-a-url"
    Path(p).write_text(json.dumps(data))
    cfg = load_config(str(p))
    ok, errs = validate_config(cfg)
    assert not ok
    assert any("matrix.server" in e for e in errs)

