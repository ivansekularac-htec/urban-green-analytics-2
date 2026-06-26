# =========================
# CONNECTIONS / GLOBAL SETTINGS
# =========================

import os

POSTGRES_CONN_ID = "urbangreen_db"
MINIO_CONN_ID = "urbangreen_minio"

# BUCKET_NAME = Variable.get("minio_bucket", default_var="staging")
# SCHEMA = Variable.get("postgres_schema", default_var="app")

SCHEMA = os.getenv("POSTGRES_SCHEMA", "app")
BUCKET_NAME = os.getenv("MINIO_STAGING_BUCKET", "staging")

# =========================
# TABLE CONFIG (SOURCE OF TRUTH)
# =========================

TABLES = [
    {
        "name": "roles",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "quality_grades",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "farm_infrastructure_types",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "growing_system_types",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "crop_categories",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "sensor_types",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "farms",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "users",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "crops",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "user_roles",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "farm_crops",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "sensors",
        "schedule": "0 2 * * *",
        "cursor_column": "updated_at",
        "partition_column": None,
    },
    {
        "name": "harvests",
        "schedule": "0 * * * *",
        "cursor_column": "updated_at",
        "partition_column": "created_at",
    },
]
