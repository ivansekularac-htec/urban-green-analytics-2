"""The dependencies the graph runs against, and the two ways to build them.

The nodes never open a connection themselves. They take a `ReportDeps` and call
through it, so the same graph runs against real clients in the DAG, against
env-built clients from `run.py`, and against fakes in a test.

`from_env` reads the same environment variables the rest of the ETL reads, so
the pipeline runs standalone. `from_airflow` builds the same bundle from the
seeded Airflow connections, which is what T5.3.2 asks the DAG to use; its
imports are local so importing this module never requires Airflow.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import boto3
import clickhouse_connect
from clickhouse_connect.driver.client import Client

DEFAULT_EMAIL_FROM = "urbangreen-reports@urbangreen.local"
DEFAULT_EMAIL_TO = "executives@urbangreen.local"

# A read of a handful of aggregated rows should not run away; the client caps
# execution and result size rather than trusting the query to stay small.
_QUERY_TIMEOUT_SECONDS = 30
_MAX_RESULT_ROWS = 10_000


@dataclass(frozen=True)
class OllamaConfig:
    """Where the local model lives and how long its answer may be."""

    host: str  # host:port, no scheme
    model: str
    # Hard ceiling on generated tokens, so a run finishes predictably.
    num_predict: int
    # Above a realistic cold start, so a slow first load is not treated as a failure.
    timeout_seconds: float


@dataclass(frozen=True)
class EmailConfig:
    """The SMTP sink and the addresses the report is sent between."""

    host: str
    port: int
    sender: str
    recipient: str


@dataclass
class ReportDeps:
    """Everything the graph needs from the outside world."""

    warehouse: Client
    s3: Any  # a boto3 S3 client, or anything with put_object
    bucket: str
    ollama: OllamaConfig
    email: EmailConfig


def _ollama_from_env() -> OllamaConfig:
    return OllamaConfig(
        host=os.environ.get("OLLAMA_HOST", "urbangreen-ollama:11434"),
        model=os.environ.get("OLLAMA_MODEL", "qwen3.5:2b"),
        num_predict=int(os.environ.get("REPORT_OLLAMA_NUM_PREDICT", "800")),
        timeout_seconds=float(os.environ.get("REPORT_OLLAMA_TIMEOUT_SECONDS", "120")),
    )


def _email_from_env() -> EmailConfig:
    return EmailConfig(
        host=os.environ.get("SMTP_HOST", "urbangreen-mailpit"),
        port=int(os.environ.get("SMTP_PORT", "1025")),
        sender=os.environ.get("REPORT_EMAIL_FROM", DEFAULT_EMAIL_FROM),
        recipient=os.environ.get("REPORT_EMAIL_TO", DEFAULT_EMAIL_TO),
    )


def _clickhouse_from_env() -> Client:
    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "urbangreen-clickhouse"),
        port=int(os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")),
        username=os.environ.get("CLICKHOUSE_USER", "urbangreen"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        database=os.environ.get("CLICKHOUSE_DB", "urbangreen_dw"),
        settings=_READ_ONLY_SETTINGS,
    )


def _s3_from_env() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000"),
        aws_access_key_id=os.environ.get("MINIO_ROOT_USER", "minio"),
        aws_secret_access_key=os.environ.get("MINIO_ROOT_PASSWORD", ""),
        region_name="us-east-1",
    )


# A read-only session that also caps runtime and result size, so a bad date or a
# broken query fails loudly instead of scanning the warehouse.
_READ_ONLY_SETTINGS = {
    "readonly": 1,
    "max_execution_time": _QUERY_TIMEOUT_SECONDS,
    "max_result_rows": _MAX_RESULT_ROWS,
    "result_overflow_mode": "throw",
}


def bucket_from_env() -> str:
    return os.environ.get("MINIO_STAGING_BUCKET", "staging")


def from_env() -> ReportDeps:
    """Build the dependencies from the environment, for a standalone run."""
    return ReportDeps(
        warehouse=_clickhouse_from_env(),
        s3=_s3_from_env(),
        bucket=bucket_from_env(),
        ollama=_ollama_from_env(),
        email=_email_from_env(),
    )


def from_airflow() -> ReportDeps:
    """Build the dependencies from the seeded Airflow connections.

    ClickHouse and MinIO come from the `urbangreen_clickhouse` and
    `urbangreen_minio` connections the init script seeds; Ollama and the mail
    sink have no seeded connection, so they come from the environment as T5.3.2
    specifies. Airflow is imported here rather than at module load, so
    `run.py` and the tests do not need it.
    """
    from airflow.hooks.base import BaseHook
    from airflow.providers.amazon.aws.hooks.s3 import S3Hook

    conn = BaseHook.get_connection("urbangreen_clickhouse")
    warehouse = clickhouse_connect.get_client(
        host=conn.host,
        port=conn.port or 8123,
        username=conn.login,
        password=conn.password or "",
        database=conn.schema or "urbangreen_dw",
        settings=_READ_ONLY_SETTINGS,
    )

    s3 = S3Hook(aws_conn_id="urbangreen_minio").get_conn()

    return ReportDeps(
        warehouse=warehouse,
        s3=s3,
        bucket=bucket_from_env(),
        ollama=_ollama_from_env(),
        email=_email_from_env(),
    )
