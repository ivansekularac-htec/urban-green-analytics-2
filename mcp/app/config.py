"""Configuration settings for the Urban Green MCP service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    clickhouse_host: str = "urbangreen-clickhouse"
    clickhouse_http_port: int = 8123
    clickhouse_db: str = "urbangreen_dw"
    clickhouse_user: str = "urbangreen"
    clickhouse_password: str

    model_config = SettingsConfigDict(
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
