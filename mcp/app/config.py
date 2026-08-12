from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001

    # ClickHouse fields carry an explicit alias: env_prefix applies only to
    # fields without one, so a single model reads both MCP_* and CLICKHOUSE_*.
    clickhouse_host: str = Field("urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field("urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field("urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field("", validation_alias="CLICKHOUSE_PASSWORD")

    # Per-query guardrails applied to every session the service opens.
    clickhouse_connect_timeout: int = Field(10, validation_alias="CLICKHOUSE_CONNECT_TIMEOUT")
    clickhouse_query_timeout: int = Field(30, validation_alias="CLICKHOUSE_QUERY_TIMEOUT")
    clickhouse_max_memory_usage: int = Field(
        1_000_000_000, validation_alias="CLICKHOUSE_MAX_MEMORY_USAGE"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
