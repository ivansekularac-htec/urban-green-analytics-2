from app.config import get_settings

settings = get_settings()


def test_settings_defaults():

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8000


def test_settings_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
