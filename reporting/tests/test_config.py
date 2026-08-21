"""Tests for reporting service configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("REPORTING_HOST", "127.0.0.1")
    monkeypatch.setenv("REPORTING_PORT", "9002")

    settings = Settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 9002


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("REPORTING_HOST", raising=False)
    monkeypatch.delenv("REPORTING_PORT", raising=False)

    # _env_file=None ignores a developer's local .env, so this really tests the
    # defaults rather than whatever that file happens to hold.
    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8002


def test_report_shape_loads_from_environment(monkeypatch):
    monkeypatch.setenv("REPORTING_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("REPORTING_TOP_FARMS", "5")
    monkeypatch.setenv("REPORTING_MAX_INSIGHTS", "2")
    monkeypatch.setenv("REPORTING_NARRATIVE_MAX_CHARS", "600")
    monkeypatch.setenv("REPORTING_QUERY_TIMEOUT_SECONDS", "15")

    settings = Settings()

    assert settings.log_level == "DEBUG"
    assert settings.top_farms == 5
    assert settings.max_insights == 2
    assert settings.narrative_max_chars == 600
    assert settings.query_timeout_seconds == 15


def test_report_shape_uses_default_values(monkeypatch):
    for var in (
        "REPORTING_LOG_LEVEL",
        "REPORTING_TOP_FARMS",
        "REPORTING_MAX_INSIGHTS",
        "REPORTING_NARRATIVE_MAX_CHARS",
        "REPORTING_QUERY_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.top_farms == 3
    assert settings.max_insights == 4
    assert settings.narrative_max_chars == 1200
    assert settings.query_timeout_seconds == 30


def test_model_policy_loads_from_environment(monkeypatch):
    monkeypatch.setenv("REPORTING_LLM_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("REPORTING_LLM_NUM_PREDICT", "200")
    monkeypatch.setenv("REPORTING_LLM_TEMPERATURE", "0.7")
    monkeypatch.setenv("REPORTING_LLM_KEEP_ALIVE", "30m")

    settings = Settings()

    assert settings.llm_timeout_seconds == 45
    assert settings.llm_num_predict == 200
    assert settings.llm_temperature == 0.7
    assert settings.llm_keep_alive == "30m"


def test_model_policy_uses_default_values(monkeypatch):
    for var in (
        "REPORTING_LLM_TIMEOUT_SECONDS",
        "REPORTING_LLM_NUM_PREDICT",
        "REPORTING_LLM_TEMPERATURE",
        "REPORTING_LLM_KEEP_ALIVE",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.llm_timeout_seconds == 120
    assert settings.llm_num_predict == 400
    assert settings.llm_temperature == 0.2
    assert settings.llm_keep_alive == "10m"


def test_publishing_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("REPORTING_PUBLISH_S3", "false")
    monkeypatch.setenv("REPORTING_PUBLISH_EMAIL", "false")
    monkeypatch.setenv("REPORTING_S3_PREFIX", "reports/weekly")
    monkeypatch.setenv("REPORTING_EMAIL_FROM", "noreply@example.com")

    settings = Settings()

    assert settings.publish_s3 is False
    assert settings.publish_email is False
    assert settings.s3_prefix == "reports/weekly"
    assert settings.email_from == "noreply@example.com"


def test_publishing_settings_use_default_values(monkeypatch):
    for var in (
        "REPORTING_PUBLISH_S3",
        "REPORTING_PUBLISH_EMAIL",
        "REPORTING_S3_PREFIX",
        "REPORTING_EMAIL_FROM",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.publish_s3 is True
    assert settings.publish_email is True
    assert settings.s3_prefix == "reports/executive"
    assert settings.email_from == "reports@urbangreen.local"


def test_email_recipients_are_split_from_one_setting(monkeypatch):
    monkeypatch.setenv("REPORTING_EMAIL_TO", "one@example.com,two@example.com")

    settings = Settings()

    assert settings.email_recipients == ["one@example.com", "two@example.com"]


def test_email_recipients_drop_blank_entries(monkeypatch):
    # A trailing comma or a stray space must not become an empty address the
    # publish step then tries to send to.
    monkeypatch.setenv("REPORTING_EMAIL_TO", " one@example.com , , two@example.com ,")

    settings = Settings()

    assert settings.email_recipients == ["one@example.com", "two@example.com"]


def test_email_recipients_are_empty_when_unset(monkeypatch):
    monkeypatch.setenv("REPORTING_EMAIL_TO", "")

    settings = Settings()

    assert settings.email_recipients == []


def test_clickhouse_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "9123")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "secret")

    settings = Settings()

    assert settings.clickhouse_host == "localhost"
    assert settings.clickhouse_port == 9123
    assert settings.clickhouse_password == "secret"


def test_clickhouse_settings_use_default_values(monkeypatch):
    for var in (
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_DB",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_CONNECT_TIMEOUT",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_connect_timeout == 10


def test_stack_connection_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("OLLAMA_API_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:7b")
    monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
    monkeypatch.setenv("MINIO_STAGING_BUCKET", "reports")
    monkeypatch.setenv("MINIO_ROOT_USER", "someone")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "secret")
    monkeypatch.setenv("SMTP_HOST", "localhost")
    monkeypatch.setenv("SMTP_PORT", "2025")

    settings = Settings()

    assert settings.ollama_url == "http://localhost:11434"
    assert settings.ollama_model == "qwen3.5:7b"
    assert settings.minio_endpoint == "http://localhost:9000"
    assert settings.minio_bucket == "reports"
    assert settings.minio_access_key == "someone"
    assert settings.minio_secret_key == "secret"
    assert settings.smtp_host == "localhost"
    assert settings.smtp_port == 2025


def test_stack_connection_settings_use_default_values(monkeypatch):
    for var in (
        "OLLAMA_API_URL",
        "OLLAMA_MODEL",
        "MINIO_ENDPOINT",
        "MINIO_STAGING_BUCKET",
        "MINIO_ROOT_USER",
        "MINIO_ROOT_PASSWORD",
        "SMTP_HOST",
        "SMTP_PORT",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.ollama_url == "http://urbangreen-ollama:11434"
    assert settings.ollama_model == "qwen3.5:2b"
    assert settings.minio_endpoint == "http://urbangreen-minio:9000"
    assert settings.minio_bucket == "staging"
    assert settings.minio_access_key == "minioadmin"
    assert settings.minio_secret_key == ""
    assert settings.smtp_host == "urbangreen-mailpit"
    assert settings.smtp_port == 1025


def test_service_settings_do_not_collide_with_stack_names(monkeypatch):
    # The prefixed field and the aliased one are different settings even though
    # both read a variable containing "HOST". Setting one must not move the
    # other.
    monkeypatch.setenv("REPORTING_HOST", "127.0.0.1")
    monkeypatch.setenv("CLICKHOUSE_HOST", "warehouse.internal")

    settings = Settings()

    assert settings.host == "127.0.0.1"
    assert settings.clickhouse_host == "warehouse.internal"


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
