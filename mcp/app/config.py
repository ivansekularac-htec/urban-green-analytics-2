"""Configuration settings for the Urban Green MCP service."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    mcp_host: str
    mcp_port: int

    clickhouse_host: str
    clickhouse_http_port: int
    clickhouse_db: str
    clickhouse_user: str
    clickhouse_password: str

    model_config = SettingsConfigDict(
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
