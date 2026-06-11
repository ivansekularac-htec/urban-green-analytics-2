from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    postgres_user: str = Field(min_length=3)
    postgres_password: str = Field(min_length=1)
    postgres_db: str = Field(min_length=1)

    postgres_host: str = "localhost"

    postgres_port: int = Field(
        default=5432,
        ge=1,
        le=65535,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()