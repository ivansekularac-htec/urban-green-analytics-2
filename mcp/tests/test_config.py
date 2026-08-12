"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("CLICKHOUSE_HOST", "clickhouse.example.com")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8123")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_dw")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")
    monkeypatch.setenv("CLICKHOUSE_QUERY_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("CLICKHOUSE_MAX_MEMORY_USAGE", "268435456")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.clickhouse_host == "clickhouse.example.com"
    assert settings.clickhouse_port == 8123
    assert settings.clickhouse_db == "test_dw"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password == "test_password"
    assert settings.clickhouse_query_timeout_seconds == 60
    assert settings.clickhouse_max_memory_usage == 268435456


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HOST", raising=False)
    monkeypatch.delenv("CLICKHOUSE_HTTP_PORT", raising=False)
    monkeypatch.delenv("CLICKHOUSE_DB", raising=False)
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)
    monkeypatch.delenv("CLICKHOUSE_QUERY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("CLICKHOUSE_MAX_MEMORY_USAGE", raising=False)

    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_query_timeout_seconds == 30
    assert settings.clickhouse_max_memory_usage == 536_870_912


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
