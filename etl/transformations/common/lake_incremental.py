"""Incremental lake reads by extract run-window (path pruning).

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Postgres extract (Module 2a) writes::

    raw/postgres/<table>/<from>__<to>/...

where ``from`` / ``to`` are UTC stamps of the ``updated_at`` cursor window.
Rows in a run folder satisfy ``from < updated_at <= to``.

This module lists those top-level run folders and reads only windows whose
upper bound is after the caller watermark, so Spark never opens older Parquet
files. Row-level ``updated_at > watermark`` filtering remains the caller's job
for partially overlapped windows.

Parquet is opened via explicit globs (not recursiveFileLookup) so the lake
layout contract stays visible in the code.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.utils import AnalysisException

from common.constants import LAKE_ROOT

logger = logging.getLogger(__name__)

_WINDOW_FMT = "%Y%m%dT%H%M%SZ"


def _stamp_to_epoch(stamp: str) -> int:
    """Parse ``YYYYMMDDTHHMMSSZ`` to UTC epoch seconds."""
    return int(
        datetime.strptime(stamp, _WINDOW_FMT).replace(tzinfo=timezone.utc).timestamp()
    )


def _list_immediate_subdirs(spark: SparkSession, absolute_dir: str) -> list[str]:
    """Return names of immediate child directories under an S3A/HDFS path."""
    jvm_path = spark._jvm.org.apache.hadoop.fs.Path(absolute_dir)
    fs = jvm_path.getFileSystem(spark._jsc.hadoopConfiguration())

    if not fs.exists(jvm_path):
        return []

    names: list[str] = []
    for status in fs.listStatus(jvm_path):
        if status.isDirectory():
            names.append(status.getPath().getName())
    return names


def _read_paths(
    spark: SparkSession,
    paths: list[str],
    glob_suffix: str,
) -> DataFrame | None:
    """Load Parquet under each path joined with ``glob_suffix`` (e.g. ``*.parquet``)."""
    if not paths:
        return None
    globbed = [f"{p.rstrip('/')}/{glob_suffix}" for p in paths]
    try:
        return spark.read.parquet(*globbed)
    except AnalysisException:
        logger.warning(f"no readable parquet under {globbed}; skipping")
        return None


def read_postgres_since(
    spark: SparkSession,
    table: str,
    watermark: int,
) -> DataFrame | None:
    """Read ``raw/postgres/<table>/`` run-windows with ``to > watermark`` only."""
    base_uri = f"{LAKE_ROOT}/raw/postgres/{table}"
    selected: list[str] = []

    for name in sorted(_list_immediate_subdirs(spark, base_uri)):
        if "__" not in name:
            logger.warning(f"skipping non run-window entry: {base_uri}/{name}")
            continue

        _, to_stamp = name.split("__", 1)
        try:
            window_to = _stamp_to_epoch(to_stamp)
        except ValueError:
            logger.warning(f"skipping unparseable run window: {base_uri}/{name}")
            continue

        if window_to > watermark:
            selected.append(f"{base_uri}/{name}")

    if not selected:
        logger.info(
            f"no run windows for {table} with window_to > watermark={watermark}"
        )
        return None

    windows = [p.rsplit("/", 1)[-1] for p in selected]
    logger.info(
        f"table={table} watermark={watermark} "
        f"reading {len(selected)} run window(s): {windows}"
    )
    # harvests: <window>/harvest_date=YYYY-MM-DD/*.parquet
    # other (flat) extract tables: <window>/*.parquet
    glob_suffix = "harvest_date=*/*.parquet" if table == "harvests" else "*.parquet"
    return _read_paths(spark, selected, glob_suffix)


def read_kafka_since(
    spark: SparkSession,
    topic: str,
    watermark: int,
) -> DataFrame | None:
    """Read ``raw/kafka/<topic>/`` event_date partitions on/after watermark's UTC day.

    Streaming layout::

        raw/kafka/<topic>/event_date=YYYY-MM-DD/...

    Partitions strictly before the watermark's UTC calendar day are skipped.
    Callers must still filter ``timestamp > watermark``.
    """
    base_uri = f"{LAKE_ROOT}/raw/kafka/{topic}"
    wm_day = (
        datetime.fromtimestamp(watermark, tz=timezone.utc).date().isoformat()
        if watermark > 0
        else "1970-01-01"
    )

    selected: list[str] = []
    for name in sorted(_list_immediate_subdirs(spark, base_uri)):
        if not name.startswith("event_date="):
            logger.warning(f"skipping non event_date entry: {base_uri}/{name}")
            continue
        day = name.split("=", 1)[1]
        if day >= wm_day:
            selected.append(f"{base_uri}/{name}")

    if not selected:
        logger.info(
            f"no event_date partitions for {topic} on/after {wm_day} "
            f"(watermark={watermark})"
        )
        return None

    logger.info(
        f"topic={topic} watermark={watermark} wm_day={wm_day} "
        f"reading {len(selected)} partition(s)"
    )
    return _read_paths(spark, selected, "*.parquet")
