from app.config import Settings


def test_settings_defaults(monkeypatch) -> None:
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001


def test_settings_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9001")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9001
