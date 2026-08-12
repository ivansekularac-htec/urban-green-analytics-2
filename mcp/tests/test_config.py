"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_DEFAULT_ROW_LIMIT", "200")
    monkeypatch.setenv("MCP_MAX_ROW_LIMIT", "2000")
    monkeypatch.setenv("MCP_CLICKHOUSE_QUERY_TIMEOUT", "60")
    monkeypatch.setenv("MCP_CLICKHOUSE_MEMORY_LIMIT", "536870912")
    monkeypatch.setenv("CLICKHOUSE_HOST", "clickhouse-test")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8124")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_database")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings()

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
    assert settings.mcp_log_level == "DEBUG"
    assert settings.mcp_default_row_limit == 200
    assert settings.mcp_max_row_limit == 2_000
    assert settings.mcp_clickhouse_query_timeout == 60
    assert settings.mcp_clickhouse_memory_limit == 536_870_912
    assert settings.clickhouse_host == "clickhouse-test"
    assert settings.clickhouse_http_port == 8124
    assert settings.clickhouse_db == "test_database"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password == "test_password"


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("MCP_LOG_LEVEL", raising=False)
    monkeypatch.delenv("MCP_DEFAULT_ROW_LIMIT", raising=False)
    monkeypatch.delenv("MCP_MAX_ROW_LIMIT", raising=False)
    monkeypatch.delenv("MCP_CLICKHOUSE_QUERY_TIMEOUT", raising=False)
    monkeypatch.delenv("MCP_CLICKHOUSE_MEMORY_LIMIT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HTTP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_DB", raising=False)
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)

    settings = Settings()

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8001
    assert settings.mcp_log_level == "INFO"
    assert settings.mcp_default_row_limit == 100
    assert settings.mcp_max_row_limit == 1_000
    assert settings.mcp_clickhouse_query_timeout == 30
    assert settings.mcp_clickhouse_memory_limit == 536_870_912
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
