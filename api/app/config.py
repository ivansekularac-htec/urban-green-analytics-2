"""
config.py
Application configuration for the Urban Green Analytics API.

This module loads application settings from environment variables
and provides a centralized configuration object that can be used
throughout the application.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    This class defines the configuration required by the application
    and automatically loads values from the configured environment file.
    """

    postgres_user: str
    postgres_password: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str

    class Config:
        env_file = ".env"


settings = Settings()
