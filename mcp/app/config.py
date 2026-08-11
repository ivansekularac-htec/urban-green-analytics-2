"""
config.py
Application configuration for the Urban Green Analytics MCP Server.

This module loads application settings from environment variables
and provides a centralized configuration object that can be used
throughout the application.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    This class defines the configuration required by the application
    and automatically loads values from the configured environment file.
    """

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()
