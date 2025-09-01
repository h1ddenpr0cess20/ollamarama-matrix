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


def test_cli_dry_run_ok(capsys, tmp_path):
    cfg = write_cfg(tmp_path)
    code = main(["--dry-run", "-v", "--config", str(cfg)])
    captured = capsys.readouterr().out
    assert code == 0
    assert "Configuration OK" in captured
    # redacted username
    assert "\"username\": \"***:" in captured


def test_cli_dry_run_overrides(capsys, tmp_path):
    cfg = write_cfg(tmp_path)
    code = main([
        "--dry-run",
        "--config",
        str(cfg),
        "--model",
        "qwen3",
        "--ollama-url",
        "http://host:11434/api/chat",
        "--store-path",
        "st",
        "--timeout",
        "10",
        "--no-markdown",
    ])
    out = capsys.readouterr().out
    assert code == 0
    assert "Configuration OK" in out

