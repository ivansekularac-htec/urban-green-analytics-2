from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8001

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
