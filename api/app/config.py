"""
config.py
Application configuration for the Urban Green Analytics API.

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

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_schema: str
    api_version_v1: str

    @property
    def database_url(self) -> str:
        """Build the PostgreSQL database connection URL.

        Returns:
            str: SQLAlchemy-compatible PostgreSQL connection URL.
        """
        return (
            f"postgresql+psycopg2://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()
