from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    postgres_host: str = Field(..., description="Database host")
    postgres_port: int = Field(5432, description="Database port")
    postgres_user: str = Field(..., description="Database user")
    postgres_password: str = Field(..., description="Database password")
    postgres_db: str = Field(..., description="Database name")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:"
            f"{self.postgres_password}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
