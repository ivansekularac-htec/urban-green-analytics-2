"""
Application configuration settings.

Loads and validates environment variables used throughout
the application.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    postgres_host: str = Field(default="localhost")
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


settings = Settings()
