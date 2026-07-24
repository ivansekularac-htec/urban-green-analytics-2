"""Load fact_daily_farm_quality_metrics from fact_harvests.

Daily yield per farm broken down by quality grade, so a dashboard can show the
quality mix of a farm's output over time without scanning the atomic harvests.

Recomputed in full from the fact table on every run, and written to a
ReplacingMergeTree keyed on the daily grain, so any late or corrected harvest -
whatever day it lands on - is reflected without tracking which days changed.
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

TARGET_TABLE = "fact_daily_farm_quality_metrics"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        harvests = clickhouse.read_query(
            spark,
            "SELECT farm_id, farm_key, harvest_date, date_key, quality_grade_id, "
            "weight_kg FROM fact_harvests FINAL",
        )

        # Grouped on the business grain only. farm_key is the SCD2 surrogate and
        # is carried as a denormalized value, not part of the grain: a farm with
        # two versions on one day would otherwise split into two rows. max picks
        # one deterministically - which version's surrogate is stamped does not
        # change the metric, which is keyed on farm_id.
        rollup = harvests.groupBy(
            "farm_id", "harvest_date", "date_key", "quality_grade_id"
        ).agg(
            F.max("farm_key").alias("farm_key"),
            F.sum("weight_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.count(F.lit(1)).cast("int").alias("harvest_count"),
        )

        target = rollup.select(
            F.col("harvest_date").alias("metric_date"),
            "date_key",
            "farm_key",
            "farm_id",
            "quality_grade_id",
            "total_yield_kg",
            "harvest_count",
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
