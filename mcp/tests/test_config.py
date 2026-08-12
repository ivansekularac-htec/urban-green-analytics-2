"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_QUERY_DEFAULT_LIMIT", "50")
    monkeypatch.setenv("MCP_QUERY_MAX_LIMIT", "500")
    monkeypatch.setenv("CLICKHOUSE_HOST", "ch.example")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8443")

    settings = Settings(_env_file=None)

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 9000
    assert settings.mcp_log_level == "DEBUG"
    assert settings.mcp_query_default_limit == 50
    assert settings.mcp_query_max_limit == 500
    assert settings.clickhouse_host == "ch.example"
    assert settings.clickhouse_http_port == 8443


def test_settings_use_default_values(monkeypatch):
    for key in (
        "MCP_HOST",
        "MCP_PORT",
        "MCP_LOG_LEVEL",
        "MCP_QUERY_DEFAULT_LIMIT",
        "MCP_QUERY_MAX_LIMIT",
        "MCP_QUERY_TIMEOUT_SECONDS",
        "MCP_QUERY_MAX_MEMORY_BYTES",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_DB",
    ):
        monkeypatch.delenv(key, raising=False)

    settings = Settings(_env_file=None)

    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8001
    assert settings.mcp_log_level == "INFO"
    assert settings.mcp_query_default_limit == 100
    assert settings.mcp_query_max_limit == 1000
    assert settings.mcp_query_timeout_seconds == 30
    assert settings.mcp_query_max_memory_bytes == 536_870_912
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_db == "urbangreen_dw"


def test_get_settings_returns_cached_instance():
    assert get_settings() is get_settings()
