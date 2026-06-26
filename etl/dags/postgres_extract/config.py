"""
config.py
Configuration for PostgreSQL-to-MinIO extraction DAGs.

This module defines Airflow connection identifiers, source and destination
settings, extraction schedules, cursor columns, partitioning rules, and the
chunk size used for large tables.
"""

from __future__ import annotations

import os

POSTGRES_CONN_ID = os.getenv("POSTGRES_EXTRACT_CONN_ID", "urbangreen_db")
MINIO_CONN_ID = os.getenv("MINIO_EXTRACT_CONN_ID", "urbangreen_minio")
POSTGRES_SCHEMA = os.getenv("POSTGRES_EXTRACT_SCHEMA", "app")
STAGING_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")

HARVESTS_CHUNK_SIZE = int(os.getenv("HARVESTS_EXTRACT_CHUNK_SIZE", "50000"))

if HARVESTS_CHUNK_SIZE <= 0:
    raise ValueError("HARVESTS_EXTRACT_CHUNK_SIZE must be greater than zero.")

TABLE_CONFIGS = [
    {"table": "roles", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "quality_grades", "schedule": "@daily", "cursor_column": "updated_at"},
    {
        "table": "farm_infrastructure_types",
        "schedule": "@daily",
        "cursor_column": "updated_at",
    },
    {
        "table": "growing_system_types",
        "schedule": "@daily",
        "cursor_column": "updated_at",
    },
    {"table": "crop_categories", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "sensor_types", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "users", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "farms", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "crops", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "farm_crops", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "sensors", "schedule": "@daily", "cursor_column": "updated_at"},
    {"table": "user_roles", "schedule": "@daily", "cursor_column": "updated_at"},
    {
        "table": "harvests",
        "schedule": "@hourly",
        "cursor_column": "updated_at",
        "extract_strategy": "chunked",
        "chunk_size": HARVESTS_CHUNK_SIZE,
        "partition": {
            "source_column": "created_at",
            "output_name": "harvest_date",
            "source_type": "epoch_seconds",
        },
    },
]
