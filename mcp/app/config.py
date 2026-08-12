"""Configuration settings for the Urban Green MCP service."""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    host: str = Field(default="0.0.0.0", validation_alias="MCP_HOST")
    port: int = Field(default=8001, validation_alias="MCP_PORT")
    log_level: str = Field(default="INFO", validation_alias="MCP_LOG_LEVEL")

    query_timeout_seconds: int = Field(default=30, validation_alias="MCP_QUERY_TIMEOUT_SECONDS")
    query_max_memory_bytes: int = Field(
        default=500_000_000, validation_alias="MCP_QUERY_MAX_MEMORY_BYTES"
    )
    query_default_row_limit: int = Field(
        default=100, validation_alias="MCP_QUERY_DEFAULT_ROW_LIMIT"
    )
    query_max_row_limit: int = Field(default=1000, validation_alias="MCP_QUERY_MAX_ROW_LIMIT")

    clickhouse_host: str = Field(
        default="urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST"
    )
    clickhouse_http_port: int = Field(default=8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field(default="urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field(default="urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: SecretStr = Field(validation_alias="CLICKHOUSE_PASSWORD")

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
