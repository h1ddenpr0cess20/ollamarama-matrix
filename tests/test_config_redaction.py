from ollamarama.config import AppConfig, MatrixConfig, OllamaConfig, summarize


def _cfg():
    return AppConfig(
        matrix=MatrixConfig(
            server="https://matrix.org",
            username="@bot:matrix.org",
            password="hunter2",
            channels=["#room:matrix.org"],
        ),
        ollama=OllamaConfig(default_model="qwen3", personality="helper"),
    )


def test_summarize_redacts_password():
    out = summarize(_cfg())
    assert out["matrix"]["password"] == "***"
    assert "hunter2" not in str(out)


def test_summarize_keeps_username_domain_for_context():
    out = summarize(_cfg())
    # Localpart masked, domain preserved
    assert out["matrix"]["username"] == "***:matrix.org"


def test_summarize_masks_username_without_domain():
    cfg = _cfg()
    cfg.matrix.username = "plainname"
    out = summarize(cfg)
    assert out["matrix"]["username"] == "***"
