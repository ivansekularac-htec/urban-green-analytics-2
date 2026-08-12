from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    mcp_query_timeout_seconds: int = 30
    mcp_query_max_memory_bytes: int = 268_435_456  # 256 MiB; under 2 GiB server profile

    clickhouse_host: str = "urbangreen-clickhouse"
    clickhouse_http_port: int = 8123
    clickhouse_user: str = "urbangreen"
    clickhouse_password: str = ""
    clickhouse_db: str = "urbangreen_dw"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
