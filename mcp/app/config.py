"""
config.py
Service configuration for the Urban Green MCP server.

This module loads settings from environment variables and provides a
centralized configuration object used throughout the service.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service settings loaded from environment variables.

    This class defines the configuration required by the MCP server and
    automatically loads values from the configured environment file.
    """

    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001

    # extra="ignore" keeps the service from failing to start when it is handed
    # an env file that also carries variables belonging to other services.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    """Return cached service settings.

    Returns:
        Settings: Service settings loaded from environment variables.
    """
    return Settings()
