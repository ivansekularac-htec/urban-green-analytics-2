import json
import time
import uuid
from datetime import datetime, timezone

from pyspark.sql.functions import col

from common.config import (
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_URL,
    CLICKHOUSE_USER,
)

CLICKHOUSE_DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"


def get_load_state(spark):
    """
    Reads current ETL load state from ClickHouse.

    Each successful ETL execution creates a new versioned row.
    The latest version represents the current cursor.
    """

    return (
        spark.read.format("jdbc")
        .option("url", CLICKHOUSE_URL)
        .option(
            "query",
            """
            SELECT
                job_name,
                cursor_json,
                last_success_at,
                _version
            FROM warehouse_load_state
            """,
        )
        .option("user", CLICKHOUSE_USER)
        .option("password", CLICKHOUSE_PASSWORD)
        .option("driver", CLICKHOUSE_DRIVER)
        .load()
    )


def get_cursor(spark, job_name):
    """
    Returns latest cursor for a given ETL job.

    Example:
    {
        "last_batch": "20250721T120000Z"
    }
    """

    state_df = (
        get_load_state(spark)
        .filter(col("job_name") == job_name)
        .orderBy(col("_version").desc())
    )

    row = state_df.first()

    if row is None:
        return None

    return json.loads(row["cursor_json"])


def save_cursor(spark, job_name, cursor):
    """
    Saves successful ETL execution state.

    Cursor is stored as JSON because different jobs
    can have different cursor structures.
    """

    version = int(time.time() * 1000)

    data = [
        (
            job_name,
            json.dumps(cursor),
            datetime.now(timezone.utc),
            str(uuid.uuid4()),
            version,
        )
    ]

    cursor_df = spark.createDataFrame(
        data,
        [
            "job_name",
            "cursor_json",
            "last_success_at",
            "run_key",
            "_version",
        ],
    )

    (
        cursor_df.write.format("jdbc")
        .option("url", CLICKHOUSE_URL)
        .option("dbtable", "warehouse_load_state")
        .option("user", CLICKHOUSE_USER)
        .option("password", CLICKHOUSE_PASSWORD)
        .option("driver", CLICKHOUSE_DRIVER)
        .mode("append")
        .save()
    )
