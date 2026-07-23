"""Reusable DataFrame transforms for warehouse loaders.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse
"""

from __future__ import annotations

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

from common.constants import RUN_VERSION, SCD_END


def latest_by_key(
    df: DataFrame,
    key: str,
    order_col: str = "updated_at",
) -> DataFrame:
    """Keep one row per natural key — the highest ``order_col``.

    Used by Type-1 dimensions so re-runs converge on a single current row.
    """
    w = Window.partitionBy(key).orderBy(F.col(order_col).desc())
    return (
        df.withColumn("_rn", F.row_number().over(w))
        .filter(F.col("_rn") == 1)
        .drop("_rn")
    )


def build_scd2(
    df: DataFrame,
    natural_key: str,
    order_col: str = "updated_at",
) -> DataFrame:
    """Build SCD2 version rows from a change-log DataFrame.

    Each distinct ``order_col`` becomes a version:
    ``valid_from`` = that timestamp, ``valid_to`` = next version (or open end),
    ``is_current`` = 1 on the latest version. Deterministic from source data,
    so re-runs produce identical (key, valid_from) rows and ReplacingMergeTree
    converges without permanent duplicates.
    """
    w = Window.partitionBy(natural_key).orderBy(F.col(order_col).asc())
    nxt = F.lead(order_col).over(w)
    return (
        df.withColumn("valid_from", F.timestamp_seconds(F.col(order_col)))
        .withColumn(
            "valid_to",
            F.when(nxt.isNotNull(), F.timestamp_seconds(nxt)).otherwise(
                F.to_timestamp(F.lit(SCD_END))
            ),
        )
        .withColumn(
            "is_current",
            F.when(nxt.isNull(), F.lit(1)).otherwise(F.lit(0)).cast("tinyint"),
        )
        .withColumn("_version", F.lit(RUN_VERSION))
    )


def with_date_time_keys(df: DataFrame, ts_col: str) -> DataFrame:
    """Add ``date_key`` (yyyyMMdd) and ``time_key`` (hour * 100 + minute)."""
    return df.withColumn(
        "date_key", F.date_format(F.col(ts_col), "yyyyMMdd").cast("int")
    ).withColumn("time_key", (F.hour(ts_col) * 100 + F.minute(ts_col)).cast("int"))
