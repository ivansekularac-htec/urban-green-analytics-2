from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001
    log_level: str = "INFO"

    # Row limits this service applies to the queries it runs.
    default_row_limit: int = 100
    max_row_limit: int = 1000

    # Per-query policy owned by this service, not by ClickHouse.
    query_timeout_seconds: int = 30
    query_max_memory_bytes: int = 536_870_912

    # Connection details are shared with the rest of the stack, so they carry an
    # explicit alias: env_prefix applies only to fields without one, which lets a
    # single model read both MCP_* and CLICKHOUSE_*.
    clickhouse_host: str = Field("urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field("urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field("urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field("", validation_alias="CLICKHOUSE_PASSWORD")
    clickhouse_connect_timeout: int = Field(10, validation_alias="CLICKHOUSE_CONNECT_TIMEOUT")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="MCP_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
