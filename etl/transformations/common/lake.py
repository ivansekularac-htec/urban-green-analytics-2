"""Read raw Parquet from the MinIO lake.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse
"""

from __future__ import annotations

import logging

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.utils import AnalysisException

from common.constants import LAKE_ROOT

logger = logging.getLogger(__name__)


def _read_glob(spark: SparkSession, glob_path: str) -> DataFrame | None:
    """Read Parquet via an explicit glob; return None if nothing matches."""
    try:
        return spark.read.parquet(glob_path)
    except AnalysisException:
        logger.warning(f"no data under {glob_path}; skipping")
        return None


def read_postgres(spark: SparkSession, table: str) -> DataFrame | None:
    """Read ``raw/postgres/<table>/<run_window>/*.parquet`` from the lake."""
    return _read_glob(spark, f"{LAKE_ROOT}/raw/postgres/{table}/*/*.parquet")


def read_kafka(spark: SparkSession, topic: str) -> DataFrame | None:
    """Read ``raw/kafka/<topic>/event_date=*/*.parquet`` from the lake."""
    return _read_glob(spark, f"{LAKE_ROOT}/raw/kafka/{topic}/*/*.parquet")
