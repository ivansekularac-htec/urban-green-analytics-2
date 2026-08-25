"""Configuration for the executive report pipeline."""

import os


def clickhouse_host() -> str:
    """Return the ClickHouse host for standalone execution."""
    return os.environ.get(
        "CLICKHOUSE_HOST",
        "urbangreen-clickhouse",
    )


def clickhouse_port() -> int:
    """Return the ClickHouse HTTP port."""
    return int(
        os.environ.get(
            "CLICKHOUSE_HTTP_PORT",
            "8123",
        )
    )


def clickhouse_user() -> str:
    """Return the ClickHouse username."""
    return os.environ["CLICKHOUSE_USER"]


def clickhouse_password() -> str:
    """Return the ClickHouse password."""
    return os.environ["CLICKHOUSE_PASSWORD"]


def clickhouse_database() -> str:
    """Return the ClickHouse database name."""
    return os.environ.get(
        "CLICKHOUSE_DB",
        "urbangreen_dw",
    )


def minio_endpoint() -> str:
    """Return the MinIO endpoint for standalone execution."""
    return os.environ.get(
        "MINIO_ENDPOINT",
        "http://urbangreen-minio:9000",
    )


def minio_access_key() -> str:
    """Return the MinIO access key."""
    return os.environ["MINIO_ROOT_USER"]


def minio_secret_key() -> str:
    """Return the MinIO secret key."""
    return os.environ["MINIO_ROOT_PASSWORD"]


def minio_staging_bucket() -> str:
    """Return the staging bucket used for reports."""
    return os.environ.get(
        "MINIO_STAGING_BUCKET",
        "staging",
    )


def ollama_base_url() -> str:
    """Return the Ollama API base URL."""
    return os.environ.get(
        "OLLAMA_BASE_URL",
        "http://urbangreen-ollama:11434",
    ).rstrip("/")


def ollama_model() -> str:
    """Return the Ollama model used for summarization."""
    return os.environ.get(
        "OLLAMA_MODEL",
        "qwen3.5:2b",
    )


def ollama_timeout_seconds() -> int:
    """Return the Ollama request timeout."""
    return int(
        os.environ.get(
            "OLLAMA_TIMEOUT_SECONDS",
            "120",
        )
    )


def report_smtp_host() -> str:
    """Return the SMTP host used for report delivery."""
    return os.environ.get(
        "REPORT_SMTP_HOST",
        "urbangreen-mailpit",
    )


def report_smtp_port() -> int:
    """Return the SMTP port used for report delivery."""
    return int(
        os.environ.get(
            "REPORT_SMTP_PORT",
            "1025",
        )
    )


def report_email_from() -> str:
    """Return the report sender address."""
    return os.environ.get(
        "REPORT_EMAIL_FROM",
        "reports@urbangreen.local",
    )


def report_email_to() -> str:
    """Return the configured report recipients."""
    return os.environ.get(
        "REPORT_EMAIL_TO",
        "executive@urbangreen.local",
    )
