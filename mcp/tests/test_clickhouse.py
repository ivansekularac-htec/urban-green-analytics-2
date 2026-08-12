"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    """Verify that settings are loaded from environment variables."""
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "9001")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_db")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")
    monkeypatch.setenv("CLICKHOUSE_QUERY_TIMEOUT", "15")
    monkeypatch.setenv("CLICKHOUSE_MAX_MEMORY_USAGE", "100000000")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000

    assert settings.clickhouse_host == "localhost"
    assert settings.clickhouse_http_port == 9001
    assert settings.clickhouse_db == "test_db"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password.get_secret_value() == "test_password"
    assert settings.clickhouse_query_timeout == 15
    assert settings.clickhouse_max_memory_usage == 100_000_000


def test_settings_use_default_values(monkeypatch):
    """Verify that non-secret settings use their default values."""
    env_vars = [
        "MCP_HOST",
        "MCP_PORT",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_DB",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_QUERY_TIMEOUT",
        "CLICKHOUSE_MAX_MEMORY_USAGE",
    ]

    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001
    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_query_timeout == 30
    assert settings.clickhouse_max_memory_usage == 500_000_000


def test_get_settings_returns_cached_instance():
    """Verify that application settings are cached."""
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
