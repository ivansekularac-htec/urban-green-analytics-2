"""Job runner helpers for warehouse Spark loaders.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse
"""

from __future__ import annotations

from collections.abc import Callable

from pyspark.sql import SparkSession

from common.spark import build_spark


def run_job(app_name: str, fn: Callable[[SparkSession], None]) -> None:
    """Build a SparkSession, run ``fn(spark)``, always stop the session."""
    spark = build_spark(app_name)
    try:
        fn(spark)
    finally:
        spark.stop()
