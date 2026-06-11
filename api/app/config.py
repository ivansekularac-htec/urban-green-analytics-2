from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_HOST: str = Field(..., description="Database host")
    POSTGRES_PORT: int = Field(5432, description="Database port")
    POSTGRES_USER: str = Field(..., description="Database user")
    POSTGRES_PASSWORD: str = Field(..., description="Database password")
    POSTGRES_DB: str = Field(..., description="Database name")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:"
            f"{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:"
            f"{self.POSTGRES_PORT}/"
            f"{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
