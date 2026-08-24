"""Environment-backed settings for the executive report pipeline."""

import os
from dataclasses import dataclass
from functools import lru_cache
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ClickHouseSettings:
    """Connection settings for the UrbanGreen warehouse."""

    host: str
    port: int
    database: str
    user: str
    password: str


@dataclass(frozen=True, slots=True)
class OllamaSettings:
    """Connection and output limits for local model inference."""

    base_url: str
    model: str
    max_tokens: int
    timeout_seconds: float


@dataclass(frozen=True, slots=True)
class MinioSettings:
    """Connection and target bucket settings for report publishing."""

    endpoint: str
    access_key: str
    secret_key: str
    staging_bucket: str


@dataclass(frozen=True, slots=True)
class EmailSettings:
    """SMTP settings for delivery to the local Mailpit inbox."""

    host: str
    port: int
    sender: str
    recipients: tuple[str, ...]
    timeout_seconds: float


def _required_env(name: str) -> str:
    """Return a required environment value or fail with a clear message."""

    value = os.getenv(name)
    if value is None or not value.strip():
        raise RuntimeError(f"Required environment variable is not set: {name}")
    return value


def _positive_int(name: str, default: str) -> int:
    """Read a strictly positive integer setting."""

    raw_value = os.getenv(name, default)
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _positive_float(name: str, default: str) -> float:
    """Read a strictly positive floating-point setting."""

    raw_value = os.getenv(name, default)
    try:
        value = float(raw_value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be a number") from exc

    if value <= 0:
        raise RuntimeError(f"{name} must be greater than zero")
    return value


def _http_url(name: str, default: str) -> str:
    """Read and normalize an HTTP service URL."""

    value = os.getenv(name, default).strip().rstrip("/")
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"{name} must be a valid HTTP or HTTPS URL")
    return value


@lru_cache(maxsize=1)
def get_clickhouse_settings() -> ClickHouseSettings:
    """Load ClickHouse settings once per process."""

    port = _positive_int("CLICKHOUSE_HTTP_PORT", "8123")
    if port > 65_535:
        raise RuntimeError("CLICKHOUSE_HTTP_PORT must be at most 65535")

    return ClickHouseSettings(
        host=os.getenv("CLICKHOUSE_HOST", "urbangreen-clickhouse"),
        port=port,
        database=os.getenv("CLICKHOUSE_DB", "urbangreen_dw"),
        user=_required_env("CLICKHOUSE_USER"),
        password=_required_env("CLICKHOUSE_PASSWORD"),
    )


@lru_cache(maxsize=1)
def get_ollama_settings() -> OllamaSettings:
    """Load Ollama settings once per process."""

    model = os.getenv("OLLAMA_MODEL", "qwen3.5:2b").strip()
    if not model:
        raise RuntimeError("OLLAMA_MODEL must not be empty")

    return OllamaSettings(
        base_url=_http_url(
            "OLLAMA_HOST",
            "http://urbangreen-ollama:11434",
        ),
        model=model,
        max_tokens=_positive_int("OLLAMA_MAX_TOKENS", "400"),
        timeout_seconds=_positive_float("OLLAMA_TIMEOUT_SECONDS", "120"),
    )


@lru_cache(maxsize=1)
def get_minio_settings() -> MinioSettings:
    """Load MinIO settings once per process."""

    return MinioSettings(
        endpoint=_http_url("MINIO_ENDPOINT", "http://urbangreen-minio:9000"),
        access_key=_required_env("MINIO_ROOT_USER"),
        secret_key=_required_env("MINIO_ROOT_PASSWORD"),
        staging_bucket=os.getenv("MINIO_STAGING_BUCKET", "staging"),
    )


@lru_cache(maxsize=1)
def get_email_settings() -> EmailSettings:
    """Load local SMTP delivery settings once per process."""

    port = _positive_int("SMTP_PORT", "1025")
    if port > 65_535:
        raise RuntimeError("SMTP_PORT must be at most 65535")

    recipients = tuple(
        address.strip()
        for address in os.getenv(
            "REPORT_EMAIL_TO",
            "executives@urbangreen.local",
        ).split(",")
        if address.strip()
    )
    if not recipients:
        raise RuntimeError("REPORT_EMAIL_TO must contain at least one address")

    sender = os.getenv("REPORT_EMAIL_FROM", "reports@urbangreen.local").strip()
    if not sender:
        raise RuntimeError("REPORT_EMAIL_FROM must not be empty")

    return EmailSettings(
        host=os.getenv("SMTP_HOST", "urbangreen-mailpit"),
        port=port,
        sender=sender,
        recipients=recipients,
        timeout_seconds=_positive_float("SMTP_TIMEOUT_SECONDS", "15"),
    )
