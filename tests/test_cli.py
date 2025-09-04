import json
from pathlib import Path

import pytest

from ollamarama.cli import main


def write_cfg(tmp_path: Path) -> Path:
    data = {
        "matrix": {
            "server": "https://matrix.org",
            "username": "@bot:matrix.org",
            "password": "x",
            "channels": ["#room:matrix.org"],
            "admins": [],
            "store_path": "store",
        },
        "ollama": {
            "api_url": "http://localhost:11434/api/chat",
            "models": {"qwen3": "qwen3"},
            "default_model": "qwen3",
            "prompt": ["you are ", "."],
            "personality": "a helpful assistant",
            "history_size": 24,
            "timeout": 30,
            "options": {"temperature": 0.5},
        },
        "markdown": True,
    }
    p = tmp_path / "cfg.json"
    p.write_text(json.dumps(data))
    return p


def test_cli_missing_config_file(capsys):
    code = main(["--config", "nonexistent.json"])
    out = capsys.readouterr().out
    assert code == 2
    assert "Config file not found:" in out


def test_cli_invalid_config_fails_validation(tmp_path, capsys):
    # Write an invalid config (missing required fields)
    bad = {
        "matrix": {
            "server": "not-a-url",
            "username": "",
            "password": "",
            "channels": [],
            "admins": [],
            "store_path": "store",
        },
        "ollama": {
            "api_url": "http://localhost:11434/api/chat",
            "models": {},
            "default_model": "",  # invalid
            "prompt": ["you are ", "."],
            "personality": "",
            "history_size": 0,
            "timeout": 30,
        },
        "markdown": True,
    }
    p = tmp_path / "bad.json"
    p.write_text(json.dumps(bad))

    code = main(["--config", str(p)])
    out = capsys.readouterr().out
    assert code == 2
    assert "Configuration errors:" in out
