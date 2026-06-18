"""
config.py
Application configuration for the Urban Green Analytics API.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """

    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int = 5432
    postgres_db: str
    postgres_schema: str

    api_v1_prefix: str = "/api/v1"

    api_app_superuser_username: str = Field(default="admin@example.com")
    api_app_superuser_password: str = Field(default="admin12345")
    jwt_secret_key: str = Field(default="development-secret-key")

    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1440

    @property
    def database_url(self) -> str:
        """
        Build the PostgreSQL database connection URL.

        Returns:
            str: SQLAlchemy-compatible PostgreSQL connection URL.
        """
        return (
            "postgresql+psycopg2://"
            f"{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    model_config = SettingsConfigDict(env_file=".env")


@lru_cache
def get_settings() -> Settings:
    """
    Return cached application settings.

    Returns:
        Settings: Application settings loaded from environment variables.
    """
    return Settings()
