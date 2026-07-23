"""Fact-job watermark (cursor) helpers.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Call ``set_watermark`` only after a successful ``write_table``. A crash between
write and set causes a clean replay of the same slice; ReplacingMergeTree on
the fact table removes temporary duplicates on merge.
"""

from __future__ import annotations

from pyspark.sql import SparkSession

from common.clickhouse import read_sql, write_table
from common.constants import RUN_VERSION


def get_watermark(spark: SparkSession, job_name: str) -> int:
    """Return the last successful watermark for ``job_name``, or 0 if none."""
    df = read_sql(
        spark,
        "SELECT max(watermark_value) AS w FROM watermarks FINAL "
        f"WHERE job_name = '{job_name}'",
    )
    row = df.collect()[0]
    return int(row["w"]) if row["w"] is not None else 0


def set_watermark(
    spark: SparkSession,
    job_name: str,
    value: int,
    rows_loaded: int,
) -> None:
    """Advance the watermark after a successful fact write."""
    wm = spark.createDataFrame(
        [(job_name, int(value), int(rows_loaded), RUN_VERSION)],
        "job_name string, watermark_value long, rows_loaded long, _version long",
    )
    write_table(wm, "watermarks")
