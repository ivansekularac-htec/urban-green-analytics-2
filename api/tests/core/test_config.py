"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment():
    settings = Settings()

    assert settings.postgres_user == "test"
    assert settings.postgres_db == "test"
    assert settings.postgres_schema == "app"
    assert settings.postgres_port == 5432
    assert settings.api_v1_prefix == "/api/v1"


def test_database_url_is_built_from_components():
    settings = Settings(
        postgres_user="alice",
        postgres_password="secret",
        postgres_host="db.example.com",
        postgres_port=6543,
        postgres_db="urban_green",
        postgres_schema="app",
    )

    assert settings.database_url == (
        "postgresql+psycopg2://alice:secret@db.example.com:6543/urban_green"
    )


def test_get_settings_returns_cached_instance():
    assert get_settings() is get_settings()


def test_settings_load_jwt_defaults_from_environment():
    settings = Settings()
    assert settings.jwt_secret_key == "test-secret-key-for-tests-only"
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_minutes == 15
    assert settings.jwt_refresh_token_expire_minutes == 10080
