"""Minimal MCP settings; T5.2.2 expands this model."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
