"""Load fact_daily_sensor_metrics from fact_sensor_readings.

Daily reading rollup per farm and sensor type. sum_value is stored instead of a
precomputed average so the metric stays correct when re-aggregated across days:
an average of averages would weight each day equally regardless of how many
readings it held, while sum_value / reading_count always recovers the true mean.

Recomputed in full from the fact table on every run; the ReplacingMergeTree
keyed on the daily grain absorbs late readings without tracking changed days.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse
from common.spark import build_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TARGET_TABLE = "fact_daily_sensor_metrics"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        readings = clickhouse.read_query(
            spark,
            "SELECT farm_id, farm_key, sensor_type_key, reading_date, date_key, "
            "value, is_anomaly FROM fact_sensor_readings FINAL",
        )

        # farm_key carried as a denormalized value, not part of the grain -
        # see load_fact_daily_farm_quality_metrics for why.
        rollup = readings.groupBy(
            "farm_id", "sensor_type_key", "reading_date", "date_key"
        ).agg(
            F.max("farm_key").alias("farm_key"),
            F.count(F.lit(1)).cast("long").alias("reading_count"),
            F.sum("value").cast("double").alias("sum_value"),
            F.min("value").cast("double").alias("min_value"),
            F.max("value").cast("double").alias("max_value"),
            F.sum("is_anomaly").cast("long").alias("anomaly_count"),
            F.sum(F.lit(1) - F.col("is_anomaly")).cast("long").alias("in_range_count"),
        )

        target = rollup.select(
            F.col("reading_date").alias("metric_date"),
            "date_key",
            "farm_key",
            "farm_id",
            "sensor_type_key",
            "reading_count",
            "sum_value",
            "min_value",
            "max_value",
            "anomaly_count",
            "in_range_count",
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
