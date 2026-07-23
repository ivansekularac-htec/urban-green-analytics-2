import json
import time
import uuid
from datetime import datetime, timezone

from pyspark.sql import SparkSession

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings


def read_cursor(
    spark: SparkSession,
    settings: WarehouseSettings,
    job_name: str,
) -> dict[str, int]:
    """Read the latest cursor for one loader."""

    table_name = f"{settings.clickhouse_database}.warehouse_load_state"

    cursor_df = read_clickhouse_query(
        spark,
        settings,
        f"""
        SELECT cursor_json
        FROM {table_name}
        WHERE job_name = '{job_name}'
        ORDER BY _version DESC
        LIMIT 1
        """,
    )

    row = cursor_df.first()

    if row is None:
        return {}

    return json.loads(row["cursor_json"])


def save_cursor(
    spark: SparkSession,
    settings: WarehouseSettings,
    job_name: str,
    cursor: dict[str, int],
) -> None:
    """Save the cursor after a successful target write."""

    state_df = spark.createDataFrame(
        [
            (
                job_name,
                json.dumps(cursor),
                datetime.now(timezone.utc).replace(tzinfo=None),
                str(uuid.uuid4()),
                time.time_ns(),
            )
        ],
        [
            "job_name",
            "cursor_json",
            "last_success_at",
            "run_key",
            "_version",
        ],
    )

    write_clickhouse_table(
        state_df,
        settings,
        "warehouse_load_state",
    )
