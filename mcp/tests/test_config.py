from app.config import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8000


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")

    settings = Settings()

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
