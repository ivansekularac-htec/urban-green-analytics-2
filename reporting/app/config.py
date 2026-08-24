"""Settings for the reporting pipeline.

Pipeline settings are read from REPORTING_*. Connection details are shared with
the rest of the stack, so they keep the names the other services already use.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    log_level: str = "INFO"

    clickhouse_host: str = Field("urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field("urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field("urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field("", validation_alias="CLICKHOUSE_PASSWORD")

    ollama_url: str = Field("http://urbangreen-ollama:11434", validation_alias="OLLAMA_API_URL")
    ollama_model: str = Field("qwen3.5:2b", validation_alias="OLLAMA_MODEL")

    minio_endpoint: str = Field("http://urbangreen-minio:9000", validation_alias="MINIO_ENDPOINT")
    minio_bucket: str = Field("staging", validation_alias="MINIO_STAGING_BUCKET")
    minio_access_key: str = Field("minioadmin", validation_alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field("", validation_alias="MINIO_ROOT_PASSWORD")

    smtp_host: str = Field("urbangreen-mailpit", validation_alias="SMTP_HOST")
    smtp_port: int = Field(1025, validation_alias="SMTP_PORT")
    email_from: str = Field("reports@urbangreen.local", validation_alias="REPORTING_EMAIL_FROM")
    email_to: str = Field("executives@urbangreen.local", validation_alias="REPORTING_EMAIL_TO")

    @property
    def email_recipients(self) -> list[str]:
        """Return the comma-separated recipients as a list."""

        return [address.strip() for address in self.email_to.split(",") if address.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REPORTING_",
        case_sensitive=False,
        # The stack shares one .env, so it carries plenty this service does not
        # read. Without this, an unrelated variable is a startup failure.
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
