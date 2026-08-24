"""Tests for environment-backed report configuration."""

import pytest

from reports import config


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Keep cached settings isolated between tests."""

    getters = (
        config.get_clickhouse_settings,
        config.get_ollama_settings,
        config.get_minio_settings,
        config.get_email_settings,
    )
    for getter in getters:
        getter.cache_clear()
    yield
    for getter in getters:
        getter.cache_clear()


def test_ollama_defaults_target_the_compose_service(monkeypatch):
    for name in (
        "OLLAMA_HOST",
        "OLLAMA_MODEL",
        "OLLAMA_MAX_TOKENS",
        "OLLAMA_TIMEOUT_SECONDS",
    ):
        monkeypatch.delenv(name, raising=False)

    settings = config.get_ollama_settings()

    assert settings.base_url == "http://urbangreen-ollama:11434"
    assert settings.model == "qwen3.5:2b"
    assert settings.max_tokens == 400
    assert settings.timeout_seconds == 120


def test_clickhouse_credentials_are_required(monkeypatch):
    monkeypatch.delenv("CLICKHOUSE_USER", raising=False)
    monkeypatch.delenv("CLICKHOUSE_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="CLICKHOUSE_USER"):
        config.get_clickhouse_settings()


def test_email_recipients_are_parsed(monkeypatch):
    monkeypatch.setenv("REPORT_EMAIL_TO", "first@example.com, second@example.com")

    settings = config.get_email_settings()

    assert settings.recipients == ("first@example.com", "second@example.com")


def test_invalid_service_url_is_rejected(monkeypatch):
    monkeypatch.setenv("OLLAMA_HOST", "not-a-url")

    with pytest.raises(RuntimeError, match="valid HTTP"):
        config.get_ollama_settings()
