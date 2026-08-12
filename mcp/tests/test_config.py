"""Tests for application configuration."""

from app.config import Settings, get_settings

CLICKHOUSE_ENV_VARS = (
    "CLICKHOUSE_HOST",
    "CLICKHOUSE_HTTP_PORT",
    "CLICKHOUSE_DB",
    "CLICKHOUSE_USER",
    "CLICKHOUSE_PASSWORD",
)

MCP_ENV_VARS = (
    "MCP_HOST",
    "MCP_PORT",
    "MCP_LOG_LEVEL",
    "MCP_DEFAULT_ROW_LIMIT",
    "MCP_MAX_ROW_LIMIT",
    "MCP_QUERY_TIMEOUT_SECONDS",
    "MCP_QUERY_MAX_MEMORY_BYTES",
)


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_DEFAULT_ROW_LIMIT", "50")
    monkeypatch.setenv("MCP_MAX_ROW_LIMIT", "500")
    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "268435456")
    monkeypatch.setenv("CLICKHOUSE_HOST", "clickhouse-test")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "8124")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_database")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000
    assert settings.log_level == "DEBUG"
    assert settings.default_row_limit == 50
    assert settings.max_row_limit == 500
    assert settings.query_timeout_seconds == 60
    assert settings.query_max_memory_bytes == 268_435_456
    assert settings.clickhouse_host == "clickhouse-test"
    assert settings.clickhouse_port == 8124
    assert settings.clickhouse_database == "test_database"
    assert settings.clickhouse_username == "test_user"
    assert settings.clickhouse_password == "test_password"


def test_settings_use_default_values(monkeypatch):
    for env_var in MCP_ENV_VARS + CLICKHOUSE_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)

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
    assert settings.clickhouse_database == "urbangreen_dw"
    assert settings.clickhouse_username == "urbangreen"
    assert settings.clickhouse_password == ""


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
