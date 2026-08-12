from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    mcp_clickhouse_query_timeout: int = 30
    mcp_clickhouse_memory_limit: int = 536_870_912
    mcp_log_level: str = "INFO"
    mcp_default_row_limit: int = 100
    mcp_max_row_limit: int = 1000

    clickhouse_host: str = "urbangreen-clickhouse"
    clickhouse_http_port: int = 8123
    clickhouse_db: str = "urbangreen_dw"
    clickhouse_user: str = "urbangreen"
    clickhouse_password: str = ""

    model_config = SettingsConfigDict(case_sensitive=False, extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
