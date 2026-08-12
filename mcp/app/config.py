from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    clickhouse_host: str = "urbangreen-clickhouse"
    clickhouse_http_port: int = 8123
    clickhouse_db: str = "urbangreen_dw"
    clickhouse_user: str = "urbangreen"
    clickhouse_password: str = ""
    clickhouse_query_timeout: int = 30
    clickhouse_memory_limit: int = 1073741824

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
