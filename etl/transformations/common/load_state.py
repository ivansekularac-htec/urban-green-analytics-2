"""Persist and retrieve incremental loader cursors in ClickHouse."""

import json
import time
from typing import Any
from uuid import uuid4

from pyspark.sql import SparkSession

from .clickhouse import (
    execute_clickhouse_sql,
    jdbc_options,
    table_name,
)
from .config import Settings

STATE_TABLE = "warehouse_load_state"


def _quote_string(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace("'", "\\'")

    return f"'{escaped}'"


def read_cursor(
    spark: SparkSession,
    settings: Settings,
    job_name: str,
) -> dict[str, Any] | None:
    target = table_name(settings, STATE_TABLE)

    cursor_query = f"""
        (
            SELECT cursor_json
            FROM {target}
            WHERE job_name = {_quote_string(job_name)}
            ORDER BY _version DESC
            LIMIT 1
        ) AS latest_cursor
    """

    rows = (
        spark.read.format("jdbc")
        .options(**jdbc_options(settings))
        .option("dbtable", cursor_query)
        .load()
        .collect()
    )

    if not rows:
        return None

    cursor = json.loads(rows[0]["cursor_json"])

    if not isinstance(cursor, dict):
        raise ValueError(f"Invalid cursor for {job_name}: expected a JSON object")

    return cursor


def commit_cursor(
    settings: Settings,
    job_name: str,
    cursor: dict[str, Any],
) -> None:
    if not job_name.strip():
        raise ValueError("job_name must not be empty")

    cursor_json = json.dumps(
        cursor,
        separators=(",", ":"),
        sort_keys=True,
    )

    run_key = str(uuid4())
    version = time.time_ns()

    target = table_name(
        settings,
        STATE_TABLE,
    )

    execute_clickhouse_sql(
        settings,
        f"""
        INSERT INTO {target} (
            job_name,
            cursor_json,
            last_success_at,
            run_key,
            _version
        )
        VALUES (
            {_quote_string(job_name)},
            {_quote_string(cursor_json)},
            now64(3),
            toUUID({_quote_string(run_key)}),
            {version}
        )
        """,
    )
