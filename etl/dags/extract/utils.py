import os
from pathlib import Path

import yaml

# =========================
# CONNECTIONS / GLOBAL SETTINGS
# =========================

POSTGRES_CONN_ID = "urbangreen_db"
MINIO_CONN_ID = "urbangreen_minio"
SCHEMA = os.getenv("POSTGRES_SCHEMA", "app")
BUCKET_NAME = os.getenv("MINIO_STAGING_BUCKET", "staging")

# =========================
# TABLE CONFIG
# =========================

CONFIG_PATH = Path(__file__).parent / "tables.yaml"


def load_config() -> dict:
    with CONFIG_PATH.open("r") as f:
        return yaml.safe_load(f)


def load_tables() -> list[dict]:
    config = load_config()

    defaults = config.get("defaults", {})

    return [{**defaults, **table} for table in config.get("tables", [])]


def get_tables_by_schedule(schedule: str):
    tables = load_tables()
    return [t for t in tables if t["schedule"] == schedule]
