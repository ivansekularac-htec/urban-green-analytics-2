from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001

    clickhouse_host: str = Field(
        default="urbangreen-clickhouse",
        validation_alias="CLICKHOUSE_HOST",
    )
    clickhouse_port: int = Field(
        default=8123,
        validation_alias="CLICKHOUSE_HTTP_PORT",
    )
    clickhouse_db: str = Field(
        default="urbangreen_dw",
        validation_alias="CLICKHOUSE_DB",
    )
    clickhouse_user: str = Field(
        default="urbangreen",
        validation_alias="CLICKHOUSE_USER",
    )
    clickhouse_password: str = Field(
        default="",
        validation_alias="CLICKHOUSE_PASSWORD",
    )
    clickhouse_query_timeout_seconds: int = Field(
        default=30,
        validation_alias="CLICKHOUSE_QUERY_TIMEOUT_SECONDS",
    )
    clickhouse_max_memory_usage: int = Field(
        default=536_870_912,
        validation_alias="CLICKHOUSE_MAX_MEMORY_USAGE",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
