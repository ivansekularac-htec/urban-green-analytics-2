"""Shared configuration for warehouse Spark loaders.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

All connection defaults and refresh windows live here so a host/bucket/port
change does not require editing every loader.
"""

from __future__ import annotations

import os
import time

# --- MinIO / lake -------------------------------------------------------------
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "minioadmin")
STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")
LAKE_ROOT = f"s3a://{STAGING_BUCKET}"

# --- ClickHouse JDBC ----------------------------------------------------------
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "urbangreen-clickhouse")
CLICKHOUSE_HTTP_PORT = os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")
CLICKHOUSE_DB = os.environ.get("CLICKHOUSE_DB", "urbangreen_dw")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "urbangreen")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "")

CLICKHOUSE_JDBC_URL = (
    f"jdbc:clickhouse://{CLICKHOUSE_HOST}:{CLICKHOUSE_HTTP_PORT}/{CLICKHOUSE_DB}"
)
CLICKHOUSE_JDBC_DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"

# --- SCD2 / refresh windows ---------------------------------------------------
# Open-ended valid_to for the current SCD2 version (matches DDL DEFAULT).
SCD_END = "2099-12-31 23:59:59"

AGG_REFRESH_DAYS = int(os.environ.get("AGG_REFRESH_DAYS", "7"))

RUN_VERSION = int(time.time() * 1000)
