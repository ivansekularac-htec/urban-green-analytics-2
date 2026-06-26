"""
Central configuration for all Postgres tables used in the ingestion pipeline.

Each entry defines how a table is:
- extracted from Postgres
- incrementally tracked via cursor
- scheduled in Airflow
- stored in MinIO as Parquet

This is the single source of truth for DAG generation.
"""

import os

# -------------------------
# Connections
# -------------------------

POSTGRES_CONN_ID = os.getenv("POSTGRES_CONN_ID", "urbangreen_db")
MINIO_CONN_ID = os.getenv("MINIO_CONN_ID", "urbangreen_minio")

# -------------------------
# Storage
# -------------------------

STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")

TABLE_CONFIGS = [
    # =========================
    # CORE BUSINESS TABLES
    # =========================
    {
        "table": "farms",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "users",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "crops",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    # =========================
    # TRANSACTIONAL / RELATION TABLES
    # =========================
    {
        "table": "farm_crops",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "user_roles",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    # =========================
    # HARVEST DATA (HIGH FREQUENCY)
    # =========================
    {
        "table": "harvests",
        "schema": "app",
        "cursor_column": "updated_at",
        "partition_column": "created_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@hourly",
    },
    # =========================
    # SENSOR DATA
    # =========================
    {
        "table": "sensors",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    # =========================
    # LOOKUP TABLES
    # =========================
    {
        "table": "roles",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "quality_grades",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "farm_infrastructure_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "growing_system_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "crop_categories",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
    {
        "table": "sensor_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": STAGING_BUCKET,
        "schedule": "@daily",
    },
]
