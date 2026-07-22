import json
import time
import uuid

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    LongType,
    StringType,
    StructField,
    StructType,
)

from transformations.common import read_clickhouse, write_clickhouse


def get_load_state(
    spark: SparkSession,
    job_name: str,
) -> str | None:
    """
    Return the last successfully processed batch for a transformation job.

    Returns None when the job has never run.
    """

    state_df = read_clickhouse(
        spark,
        f"""
        (
            SELECT cursor_json
            FROM warehouse_load_state FINAL
            WHERE job_name = '{job_name}'
            LIMIT 1
        ) AS warehouse_load_state
        """,
    )

    rows = state_df.collect()

    if not rows:
        return None

    return json.loads(rows[0]["cursor_json"])


def set_load_state(
    spark: SparkSession,
    job_name: str,
    batch_name: str,
):
    """
    Save the latest successfully processed batch for a transformation job.
    """

    version = int(time.time() * 1000)

    schema = StructType(
        [
            StructField("job_name", StringType()),
            StructField("cursor_json", StringType()),
            StructField("run_key", StringType()),
            StructField("_version", LongType()),
        ]
    )

    state_df = spark.createDataFrame(
        [
            (
                job_name,
                json.dumps(batch_name),
                str(uuid.uuid4()),
                version,
            )
        ],
        schema=schema,
    )

    write_clickhouse(
        state_df,
        "warehouse_load_state",
    )
