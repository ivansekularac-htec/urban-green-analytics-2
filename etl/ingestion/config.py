"""
Central configuration for all Postgres tables used in the ingestion pipeline.

Each entry defines how a table is:
- extracted from Postgres
- incrementally tracked via cursor
- scheduled in Airflow
- stored in MinIO as Parquet

This is the single source of truth for DAG generation.
"""

TABLE_CONFIGS = [
    # =========================
    # CORE BUSINESS TABLES
    # =========================
    {
        "table": "farms",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "users",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "crops",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    # =========================
    # TRANSACTIONAL / RELATION TABLES
    # =========================
    {
        "table": "farm_crops",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "user_roles",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    # =========================
    # HARVEST DATA (HIGH FREQUENCY)
    # =========================
    {
        "table": "harvests",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@hourly",
    },
    # =========================
    # SENSOR DATA
    # =========================
    {
        "table": "sensors",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    # =========================
    # LOOKUP TABLES
    # =========================
    {
        "table": "roles",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "quality_grades",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "farm_infrastructure_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "growing_system_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "crop_categories",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
    {
        "table": "sensor_types",
        "schema": "app",
        "cursor_column": "updated_at",
        "bucket": "staging",
        "schedule": "@daily",
    },
]
