"""
Shared helpers and constants for Superset bootstrap modules.
"""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from superset.connectors.sqla.models import SqlaTable
    from superset.models.core import Database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [bootstrap] %(levelname)s %(message)s",
)
logger = logging.getLogger("bootstrap")

CLICKHOUSE_DATABASE_NAME = "ClickHouse Connect (Superset)"

# Stable dataset table_name values from the T4.2.6 export that expose farm_id.
EXPECTED_RLS_DATASETS = (
    "fact_daily_farm_metrics",
    "ds_daily_farm_metrics_enriched",
    "ds_daily_farm_quality",
    "ds_harvests_enriched",
    "ds_dim_farm_current",
    "ds_farm_leaderboard",
    "ds_sensor_readings",
    "ds_daily_sensor_metrics",
    "ds_sensor_inventory",
)

_summary = {"created": 0, "updated": 0, "skipped": 0}


def bump(kind: str) -> None:
    _summary[kind] = _summary.get(kind, 0) + 1


def print_summary() -> None:
    logger.info(
        "summary: created=%s updated=%s skipped=%s",
        _summary["created"],
        _summary["updated"],
        _summary["skipped"],
    )


def env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None or value == "":
        raise RuntimeError(f"Required environment variable {name} is not set")
    return value


def get_admin_role():
    from superset import security_manager

    role = security_manager.find_role("Admin")
    if role is None:
        raise RuntimeError("Built-in Admin role not found.")
    return role


def get_database(name: str = CLICKHOUSE_DATABASE_NAME) -> Database | None:
    from superset import db
    from superset.models.core import Database

    return (
        db.session.query(Database)
        .filter(Database.database_name == name)
        .one_or_none()
    )


def get_dataset(database: Database, table_name: str) -> SqlaTable | None:
    from superset import db
    from superset.connectors.sqla.models import SqlaTable

    return (
        db.session.query(SqlaTable)
        .filter(
            SqlaTable.database_id == database.id,
            SqlaTable.table_name == table_name,
        )
        .one_or_none()
    )
