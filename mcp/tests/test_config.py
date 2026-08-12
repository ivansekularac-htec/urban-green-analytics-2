"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("CLICKHOUSE_HOST", "clickhouse-test")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8124")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_database")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")
    monkeypatch.setenv("CLICKHOUSE_QUERY_TIMEOUT", "60")
    monkeypatch.setenv("CLICKHOUSE_MEMORY_LIMIT", "268435456")

    settings = Settings()

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
    assert settings.clickhouse_host == "clickhouse-test"
    assert settings.clickhouse_http_port == 8124
    assert settings.clickhouse_db == "test_database"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password == "test_password"
    assert settings.clickhouse_query_timeout == 60
    assert settings.clickhouse_memory_limit == 268435456


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HTTP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_DB", raising=False)
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)
    monkeypatch.delenv("CLICKHOUSE_QUERY_TIMEOUT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_MEMORY_LIMIT", raising=False)

    settings = Settings()

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8001
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_query_timeout == 30
    assert settings.clickhouse_memory_limit == 1073741824


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
