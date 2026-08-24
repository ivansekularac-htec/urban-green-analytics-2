"""Tests for reporting pipeline configuration."""

from app.config import Settings, get_settings


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("REPORTING_LOG_LEVEL", raising=False)

    # _env_file=None ignores a developer's local .env.
    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.ollama_model == "qwen3.5:2b"
    assert settings.minio_bucket == "staging"


def test_pipeline_settings_read_the_reporting_prefix(monkeypatch):
    monkeypatch.setenv("REPORTING_LOG_LEVEL", "DEBUG")

    assert Settings().log_level == "DEBUG"


def test_stack_settings_read_their_shared_names(monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("OLLAMA_API_URL", "http://localhost:11434")

    settings = Settings()

    assert settings.clickhouse_host == "localhost"
    assert settings.ollama_url == "http://localhost:11434"


def test_email_recipients_are_split_and_stripped(monkeypatch):
    monkeypatch.setenv("REPORTING_EMAIL_TO", " one@example.com , , two@example.com ,")

    assert Settings().email_recipients == ["one@example.com", "two@example.com"]


def test_get_settings_is_cached():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
