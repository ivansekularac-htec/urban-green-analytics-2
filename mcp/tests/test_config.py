"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    """Verify that settings are loaded from environment variables."""
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "100000000")
    monkeypatch.setenv("MCP_QUERY_DEFAULT_ROW_LIMIT", "50")
    monkeypatch.setenv("MCP_QUERY_MAX_ROW_LIMIT", "500")

    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "9001")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_db")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"

    assert settings.query_timeout_seconds == 15
    assert settings.query_max_memory_bytes == 100_000_000
    assert settings.query_default_row_limit == 50
    assert settings.query_max_row_limit == 500

    assert settings.clickhouse_host == "localhost"
    assert settings.clickhouse_http_port == 9001
    assert settings.clickhouse_db == "test_db"
    assert settings.clickhouse_user == "test_user"
    assert settings.clickhouse_password.get_secret_value() == "test_password"


def test_settings_use_default_values(monkeypatch):
    """Verify that non-secret settings use their default values."""
    env_vars = [
        "MCP_HOST",
        "MCP_PORT",
        "MCP_LOG_LEVEL",
        "MCP_QUERY_TIMEOUT_SECONDS",
        "MCP_QUERY_MAX_MEMORY_BYTES",
        "MCP_QUERY_DEFAULT_ROW_LIMIT",
        "MCP_QUERY_MAX_ROW_LIMIT",
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_DB",
        "CLICKHOUSE_USER",
    ]

    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001
    assert settings.log_level == "INFO"

    assert settings.query_timeout_seconds == 30
    assert settings.query_max_memory_bytes == 500_000_000
    assert settings.query_default_row_limit == 100
    assert settings.query_max_row_limit == 1000

    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_http_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"


def test_get_settings_returns_cached_instance(monkeypatch):
    """Verify that application settings are cached."""
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()
