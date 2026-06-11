"""
Application configuration for the Urban Green Analytics API.

This module defines and loads application settings from environment
variables using Pydantic Settings. It provides a centralized
configuration object that can be imported throughout the application
to access environment-specific values.

The current configuration includes PostgreSQL database connection
settings used by the API to establish database connectivity.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

from functools import lru_cache

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    This class defines the configuration required by the application
    and automatically loads values from the configured environment
    file. Pydantic validates the loaded values and converts them
    to the appropriate Python types.

    Attributes:
        postgres_host:
            Hostname or IP address of the PostgreSQL server.

        postgres_port:
            Port used to connect to the PostgreSQL server.

        postgres_user:
            Database username used for authentication.

        postgres_password:
            Database password used for authentication.

        postgres_db:
            Name of the PostgreSQL database used by the application.
    """

    postgres_host: str
    postgres_port: int
    postgres_user: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(
        # Load configuration values from the local .env file.
        env_file=".env",
        # Ignore unrelated environment variables that are not
        # explicitly defined in this settings model.
        extra="ignore",
    )


# Shared application settings instance.
#
# Import this object wherever configuration values are needed:
#
#     from app.config import settings
#
# Example:
#
#     settings.postgres_host
#
@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()