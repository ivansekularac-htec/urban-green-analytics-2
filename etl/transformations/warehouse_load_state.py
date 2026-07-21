import json
import time
import uuid

from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp, lit

from transformations.common import read_clickhouse, write_clickhouse


def get_load_state(
    spark: SparkSession,
    job_name: str,
) -> dict | None:
    """
    Read the latest successful load state for a job.
    """

    state_df = read_clickhouse(
        spark,
        "warehouse_load_state FINAL",
    ).filter(f"job_name = '{job_name}'")

    rows = state_df.collect()

    if not rows:
        return None

    return json.loads(rows[0]["cursor_json"])


def update_load_state(
    spark: SparkSession,
    job_name: str,
    cursor: dict,
):
    """
    Store successful warehouse load state.
    """

    load_version = int(time.time() * 1000)

    state_df = spark.createDataFrame(
        [
            (
                job_name,
                json.dumps(cursor),
                str(uuid.uuid4()),
            )
        ],
        [
            "job_name",
            "cursor_json",
            "run_key",
        ],
    )

    state_df = state_df.withColumn(
        "last_success_at",
        current_timestamp(),
    ).withColumn(
        "_version",
        lit(load_version),
    )

    write_clickhouse(
        state_df,
        "warehouse_load_state",
    )
