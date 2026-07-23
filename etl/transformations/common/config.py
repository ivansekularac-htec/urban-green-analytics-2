"""Environment-driven configuration shared by every warehouse loader.

Values come from the container environment so a loader behaves the same whether
it is submitted by the orchestrator or run by hand with spark-submit.
"""

import os

# --- MinIO (raw zone) --------------------------------------------------------

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minio")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "")

# The streaming job sets MINIO_ENDPOINT directly; the Airflow container only
# carries the port, so fall back to building the in-network endpoint from it.
MINIO_ENDPOINT = os.environ.get(
    "MINIO_ENDPOINT",
    f"http://urbangreen-minio:{os.environ.get('MINIO_API_PORT', '9000')}",
)

RAW_POSTGRES_PREFIX = f"s3a://{MINIO_STAGING_BUCKET}/raw/postgres"
RAW_KAFKA_PREFIX = f"s3a://{MINIO_STAGING_BUCKET}/raw/kafka"

# --- ClickHouse (warehouse) --------------------------------------------------

CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "urbangreen-clickhouse")
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "urbangreen_dw")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "urbangreen")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "")

# HTTP port inside the container. The ClickHouse JDBC driver speaks HTTP, and
# loaders reach the server over the compose network, so the host-side port
# mapping (CLICKHOUSE_HTTP_PORT / CLICKHOUSE_TCP_PORT_HOST) does not apply here.
CLICKHOUSE_HTTP_PORT = "8123"

# --- Business rules ----------------------------------------------------------

# Quality grade codes that count as premium in dashboard quality-mix metrics.
# Keyed on code rather than name: the code is a stable identifier, while the
# name is display text that can be renamed or translated without notice.
PREMIUM_QUALITY_CODES = frozenset({"A"})
