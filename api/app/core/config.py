"""
Application configuration for the Urban Green Analytics API.

This module loads environment variables from the local .env file and exposes
a cached settings factory for use across the application.
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

    The database_url property builds the SQLAlchemy PostgreSQL connection URL
    from the individual PostgreSQL settings.
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

    @property
    def database_url(self) -> str:
        """Return the SQLAlchemy PostgreSQL database URL."""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}"
            f"/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()
