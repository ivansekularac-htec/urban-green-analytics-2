"""Tests for the MCP service configuration."""

from app.config import Settings


def test_settings_defaults(monkeypatch) -> None:
    """Verify that default settings are used when environment variables are absent."""
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HTTP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_DB", raising=False)
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test-password")

    settings = Settings()

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8001
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == "test-password"


def test_environment_overrides_defaults(monkeypatch) -> None:
    """Verify that environment variables override default settings."""
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test-password")

    settings = Settings()

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
