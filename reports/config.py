"""Configuration for the UrbanGreen executive report pipeline."""

import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class ClickHouseSettings:
    """ClickHouse connection settings."""

    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(frozen=True)
class OllamaSettings:
    """Ollama inference settings."""

    host: str
    port: int
    model: str
    max_tokens: int

    @property
    def url(self) -> str:
        """Return the Ollama service URL."""
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class MinioSettings:
    """MinIO publishing settings."""

    endpoint: str
    user: str
    password: str
    staging_bucket: str


@dataclass(frozen=True)
class EmailSettings:
    """SMTP settings for report delivery."""

    host: str
    port: int
    sender: str
    recipients: tuple[str, ...]
    use_tls: bool
    user: str | None
    password: str | None


def _required_env(name: str) -> str:
    """Return a required environment variable."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Required environment variable is not set: {name}")
    return value


@lru_cache(maxsize=1)
def get_clickhouse_settings() -> ClickHouseSettings:
    """Load and cache ClickHouse settings."""
    return ClickHouseSettings(
        host=_required_env("CLICKHOUSE_HOST"),
        port=int(_required_env("CLICKHOUSE_HTTP_PORT")),
        database=_required_env("CLICKHOUSE_DB"),
        user=_required_env("CLICKHOUSE_USER"),
        password=_required_env("CLICKHOUSE_PASSWORD"),
    )


@lru_cache(maxsize=1)
def get_ollama_settings() -> OllamaSettings:
    """Load and cache Ollama settings."""
    return OllamaSettings(
        host=_required_env("OLLAMA_HOST"),
        port=int(_required_env("OLLAMA_API_PORT")),
        model=_required_env("OLLAMA_MODEL"),
        max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "400")),
    )


@lru_cache(maxsize=1)
def get_minio_settings() -> MinioSettings:
    """Load and cache MinIO settings."""
    return MinioSettings(
        endpoint=_required_env("MINIO_ENDPOINT"),
        user=_required_env("MINIO_ROOT_USER"),
        password=_required_env("MINIO_ROOT_PASSWORD"),
        staging_bucket=_required_env("MINIO_STAGING_BUCKET"),
    )


@lru_cache(maxsize=1)
def get_email_settings() -> EmailSettings:
    """Load and cache SMTP settings."""
    recipients = tuple(
        value.strip()
        for value in _required_env("REPORT_EMAIL_TO").split(",")
        if value.strip()
    )

    return EmailSettings(
        host=_required_env("SMTP_HOST"),
        port=int(_required_env("SMTP_PORT")),
        sender=_required_env("SMTP_FROM"),
        recipients=recipients,
        use_tls=os.getenv("SMTP_USE_TLS", "false").lower() == "true",
        user=os.getenv("SMTP_USER"),
        password=os.getenv("SMTP_PASSWORD"),
    )
