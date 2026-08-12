"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_DEFAULT_ROW_LIMIT", "50")
    monkeypatch.setenv("MCP_MAX_ROW_LIMIT", "500")
    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "268435456")
    monkeypatch.setenv("CLICKHOUSE_HOST", "clickhouse.example.com")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8124")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_dw")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"
    assert settings.default_row_limit == 50
    assert settings.max_row_limit == 500
    assert settings.query_timeout_seconds == 60
    assert settings.query_max_memory_bytes == 268435456
    assert settings.clickhouse_host == "clickhouse.example.com"
    assert settings.clickhouse_port == 8124
    assert settings.clickhouse_db == "test_dw"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password == "test_password"


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("MCP_LOG_LEVEL", raising=False)
    monkeypatch.delenv("MCP_DEFAULT_ROW_LIMIT", raising=False)
    monkeypatch.delenv("MCP_MAX_ROW_LIMIT", raising=False)
    monkeypatch.delenv("MCP_QUERY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("MCP_QUERY_MAX_MEMORY_BYTES", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HTTP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_DB", raising=False)
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001
    assert settings.log_level == "INFO"
    assert settings.default_row_limit == 100
    assert settings.max_row_limit == 1000
    assert settings.query_timeout_seconds == 30
    assert settings.query_max_memory_bytes == 536_870_912
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
