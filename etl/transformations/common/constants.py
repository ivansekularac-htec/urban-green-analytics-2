"""Shared configuration for warehouse Spark loaders.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

All connection defaults and refresh windows live here so a host/bucket/port
change does not require editing every loader.
"""

from __future__ import annotations

import os
import time


def _require(name: str) -> str:
    """Return a required env var or raise if missing / empty."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing required env var: {name}")
    return value


# --- MinIO / lake -------------------------------------------------------------
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = _require("MINIO_ROOT_USER")
MINIO_SECRET_KEY = _require("MINIO_ROOT_PASSWORD")
STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")
LAKE_ROOT = f"s3a://{STAGING_BUCKET}"

# --- ClickHouse JDBC ----------------------------------------------------------
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "urbangreen-clickhouse")
CLICKHOUSE_HTTP_PORT = os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "urbangreen_dw")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "urbangreen")
CLICKHOUSE_PASSWORD = _require("CLICKHOUSE_PASSWORD")

CLICKHOUSE_JDBC_URL = (
    f"jdbc:clickhouse://{CLICKHOUSE_HOST}:{CLICKHOUSE_HTTP_PORT}/{CLICKHOUSE_DB}"
)
CLICKHOUSE_JDBC_DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"

# --- SCD2 / refresh windows ---------------------------------------------------
# Open-ended valid_to for the current SCD2 version (matches DDL DEFAULT).
SCD_END = "2099-12-31 23:59:59"
SCD_START = "1970-01-01 00:00:00"

# Sliding window for aggregate fact refresh: each run recomputes the last N days
# from atomic facts (FINAL) so late/corrected rows inside the window are reflected.
# No watermark — older days outside the window are left untouched (cost vs freshness).
AGG_REFRESH_DAYS = int(os.environ.get("AGG_REFRESH_DAYS", "7"))

RUN_VERSION = int(time.time() * 1000)
