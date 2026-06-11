"""
@File: config.py
Application configuration for the Urban Green Analytics API.

This module loads environment variables from the local .env file and exposes
a cached settings instance for use across the application.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        postgres_host (str): PostgreSQL host address.
        postgres_port (int): PostgreSQL port.
        postgres_user (str): PostgreSQL username.
        postgres_password (str): PostgreSQL password.
        postgres_db (str): PostgreSQL database name.
    """

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance.

    The settings object is cached so environment variables are parsed only once
    during the application lifecycle.

    Returns:
        Settings: The application settings loaded from environment variables.
    """
    return Settings()


settings = get_settings()
