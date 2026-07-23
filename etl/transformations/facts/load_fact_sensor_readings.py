"""Incremental loader for fact_sensor_readings.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse

Source: raw/kafka/sensor_readings/
Target: urbangreen_dw.fact_sensor_readings

Reads only rows with timestamp greater than the last successful watermark.
Sets is_anomaly from current sensor-type optimal bounds.
Advances watermarks only after the JDBC write succeeds, and only when every
row resolved its dimension keys (otherwise the same slice is replayed).

Run after load_dim_farm, load_dim_sensor, and load_dim_sensor_type.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from common.clickhouse import read_sql, write_table
from common.jobs import run_job
from common.lake_incremental import read_kafka_since
from common.transforms import with_date_time_keys
from common.watermarks import get_watermark, set_watermark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

JOB = "fact_sensor_readings"


def _load(spark: SparkSession) -> None:
    """Load new sensor readings since the last watermark into fact_sensor_readings."""
    wm = get_watermark(spark, JOB)
    raw = read_kafka_since(spark, "sensor_readings", wm)
    if raw is None:
        print(f"no new sensor_readings partitions since watermark={wm}; skipping")
        return
    slice_ = (
        raw.filter(F.col("timestamp") > wm)
        .dropDuplicates(["farm_sensor_id", "timestamp"])
        .cache()
    )

    stats = slice_.agg(
        F.max("timestamp").alias("hi"),
        F.count("*").alias("cnt"),
    ).collect()[0]
    new_wm, cnt = stats["hi"], int(stats["cnt"])

    if cnt == 0:
        slice_.unpersist()
        print(f"no new rows since watermark={wm}; skipping")
        return

    sensor_dim = read_sql(
        spark,
        "SELECT sensor_id, sensor_key, farm_key FROM dim_sensor FINAL "
        "WHERE is_current = 1",
    )
    st_dim = read_sql(
        spark,
        "SELECT sensor_type_id, sensor_type_key, optimal_min, optimal_max "
        "FROM dim_sensor_type FINAL WHERE is_current = 1",
    )

    r = slice_.withColumn("reading_ts", F.timestamp_seconds("timestamp")).withColumn(
        "reading_date", F.to_date("reading_ts")
    )
    r = with_date_time_keys(r, "reading_ts")

    r = r.join(
        F.broadcast(sensor_dim),
        r["farm_sensor_id"] == sensor_dim["sensor_id"],
        "left",
    ).join(F.broadcast(st_dim), "sensor_type_id", "left")

    # Deterministic key (Spark has no cityHash64; xxhash64 is stable across re-runs).
    reading_key = F.abs(
        F.xxhash64(
            F.col("farm_sensor_id").cast("long"),
            F.col("timestamp").cast("long"),
        )
    )
    is_anomaly = F.coalesce(
        (
            (F.col("value") < F.col("optimal_min"))
            | (F.col("value") > F.col("optimal_max"))
        ).cast("tinyint"),
        F.lit(0),
    )

    out = r.select(
        reading_key.alias("reading_key"),
        F.coalesce(F.col("farm_key"), F.lit(0)).alias("farm_key"),
        F.col("farm_id"),
        F.coalesce(F.col("sensor_key"), F.lit(0)).alias("sensor_key"),
        F.coalesce(F.col("sensor_type_key"), F.lit(0)).alias("sensor_type_key"),
        F.col("date_key"),
        F.col("time_key"),
        F.col("reading_ts"),
        F.col("reading_date"),
        F.col("value").cast("double"),
        is_anomaly.alias("is_anomaly"),
    ).cache()

    unresolved = out.filter(
        (F.col("farm_key") == 0)
        | (F.col("sensor_key") == 0)
        | (F.col("sensor_type_key") == 0)
    ).count()

    write_table(out, "fact_sensor_readings")

    if unresolved > 0:
        out.unpersist()
        slice_.unpersist()
        print(
            f"fact_sensor_readings: wrote {cnt} rows but {unresolved} unresolved "
            f"dim key(s); watermark left at {wm} — re-run after dimensions"
        )
        return

    set_watermark(spark, JOB, int(new_wm), cnt)
    out.unpersist()
    slice_.unpersist()
    print(f"fact_sensor_readings: loaded {cnt} rows, watermark {wm} -> {new_wm}")


if __name__ == "__main__":
    run_job("load_fact_sensor_readings", _load)
