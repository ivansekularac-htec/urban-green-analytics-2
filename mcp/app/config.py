"""Configuration settings for the Urban Green MCP service."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    host: str = Field(default="0.0.0.0", validation_alias="MCP_HOST")
    port: int = Field(default=8001, validation_alias="MCP_PORT")

    clickhouse_host: str = Field(
        default="urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST"
    )
    clickhouse_http_port: int = Field(default=8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field(default="urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field(default="urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: SecretStr = Field(validation_alias="CLICKHOUSE_PASSWORD")
    clickhouse_query_timeout: int = Field(default=30, validation_alias="CLICKHOUSE_QUERY_TIMEOUT")
    clickhouse_max_memory_usage: int = Field(
        default=500_000_000, validation_alias="CLICKHOUSE_MAX_MEMORY_USAGE"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""
    return Settings()
