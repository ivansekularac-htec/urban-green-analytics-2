from app.config import Settings, get_settings


def test_settings_defaults() -> None:
    settings = Settings()
    assert settings.mcp_host == "0.0.0.0"
    assert settings.mcp_port == 8001


def test_get_settings_returns_settings() -> None:
    get_settings.cache_clear()
    settings = get_settings()
    assert isinstance(settings, Settings)
