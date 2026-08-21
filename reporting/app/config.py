"""Configuration for the reporting service.

Policy this service owns - how long the model may run, how much of the day the
report is allowed to say, where the finished document goes - is read from
REPORTING_* variables.

Connection details are shared with the rest of the stack, so they carry an
explicit alias: env_prefix applies only to fields without one, which lets a
single model read both REPORTING_* and the stack-wide CLICKHOUSE_*, OLLAMA_*,
MINIO_* and SMTP_* names the other services already use.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    host: str = "0.0.0.0"
    port: int = 8002
    log_level: str = "INFO"

    # How much of the day the report is allowed to say. These bound the
    # document, not the model: the template renders what fits in them.
    top_farms: int = 3
    max_insights: int = 4
    narrative_max_chars: int = 1200

    # Per-query policy owned by this service, not by ClickHouse. The report
    # reads pre-aggregated tables at a single date, so it needs far less room
    # than an interactive query does.
    query_timeout_seconds: int = 30

    # Local model policy. num_predict is the token ceiling that makes a run
    # finish predictably; keep_alive holds the model resident so the next day's
    # run does not pay to load it again.
    llm_timeout_seconds: int = 120
    llm_num_predict: int = 400
    llm_temperature: float = 0.2
    llm_keep_alive: str = "10m"

    # Where a finished report goes. Each sink can be switched off on its own,
    # so a stack without MinIO or without a mail server still produces one.
    publish_s3: bool = True
    publish_email: bool = True
    s3_prefix: str = "reports/executive"
    email_from: str = "reports@urbangreen.local"

    # Comma-separated, following the convention API_DEMO_OPS_FARM_IDS already
    # sets. Read it through email_recipients rather than splitting it again.
    email_to: str = "executives@urbangreen.local"

    clickhouse_host: str = Field("urbangreen-clickhouse", validation_alias="CLICKHOUSE_HOST")
    clickhouse_port: int = Field(8123, validation_alias="CLICKHOUSE_HTTP_PORT")
    clickhouse_db: str = Field("urbangreen_dw", validation_alias="CLICKHOUSE_DB")
    clickhouse_user: str = Field("urbangreen", validation_alias="CLICKHOUSE_USER")
    clickhouse_password: str = Field("", validation_alias="CLICKHOUSE_PASSWORD")
    clickhouse_connect_timeout: int = Field(10, validation_alias="CLICKHOUSE_CONNECT_TIMEOUT")

    ollama_url: str = Field("http://urbangreen-ollama:11434", validation_alias="OLLAMA_API_URL")
    ollama_model: str = Field("qwen3.5:2b", validation_alias="OLLAMA_MODEL")

    minio_endpoint: str = Field("http://urbangreen-minio:9000", validation_alias="MINIO_ENDPOINT")
    minio_bucket: str = Field("staging", validation_alias="MINIO_STAGING_BUCKET")
    minio_access_key: str = Field("minioadmin", validation_alias="MINIO_ROOT_USER")
    minio_secret_key: str = Field("", validation_alias="MINIO_ROOT_PASSWORD")

    smtp_host: str = Field("urbangreen-mailpit", validation_alias="SMTP_HOST")
    smtp_port: int = Field(1025, validation_alias="SMTP_PORT")

    @property
    def email_recipients(self) -> list[str]:
        """Return the configured recipients as a list.

        Blank entries are dropped, so a trailing comma or an empty setting
        leaves no address behind for the publish step to fail on.
        """

        return [address.strip() for address in self.email_to.split(",") if address.strip()]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="REPORTING_",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
