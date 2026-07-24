"""Load fact_farm_leaderboard from fact_daily_farm_metrics.

Ranks farms against each other within each day on three axes - total yield,
premium share and energy efficiency - and combines them into one standing. It
reads the daily farm rollup rather than the atomic facts, so the ranking is a
thin step over numbers that were already aggregated once.

The composite is a points system: on each axis a farm earns (number of farms -
rank + 1) points, so first place scores highest, and the points are summed.
composite_score is therefore higher-is-better and composite_rank 1 is the top
farm. A rank-sum would have made the ranking depend on how many farms compete
that day; points keep it comparable.

Recomputed in full from fact_daily_farm_metrics on every run so a corrected
daily metric re-ranks its day.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import Window
from pyspark.sql import functions as F

from common import clickhouse
from common.spark import build_spark

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

TARGET_TABLE = "fact_farm_leaderboard"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        recent = clickhouse.read_query(
            spark,
            "SELECT metric_date, date_key, farm_key, farm_id, total_yield_kg, "
            "premium_yield_kg, energy_kwh FROM fact_daily_farm_metrics FINAL",
        )

        has_yield = F.col("total_yield_kg") > 0
        derived = (
            recent.withColumn(
                "premium_yield_share",
                F.when(has_yield, F.col("premium_yield_kg") / F.col("total_yield_kg")).otherwise(0.0),
            )
            .withColumn(
                "energy_efficiency_kwh_per_kg",
                F.when(has_yield, F.col("energy_kwh") / F.col("total_yield_kg")).otherwise(0.0),
            )
            # Farms without yield have no meaningful efficiency, so they are
            # pushed to the bottom of the energy ranking rather than counted as
            # perfectly efficient at zero.
            .withColumn("_no_yield", F.when(has_yield, 0).otherwise(1))
        )

        by_day = Window.partitionBy("date_key")
        farm_count = F.count(F.lit(1)).over(by_day)

        yield_rank = F.rank().over(by_day.orderBy(F.col("total_yield_kg").desc()))
        quality_rank = F.rank().over(by_day.orderBy(F.col("premium_yield_share").desc()))
        energy_rank = F.rank().over(
            by_day.orderBy(F.col("_no_yield").asc(), F.col("energy_efficiency_kwh_per_kg").asc())
        )

        ranked = (
            derived.withColumn("yield_rank", yield_rank)
            .withColumn("quality_rank", quality_rank)
            .withColumn("energy_rank", energy_rank)
            .withColumn("_farm_count", farm_count)
        )

        points = (
            (F.col("_farm_count") - F.col("yield_rank") + 1)
            + (F.col("_farm_count") - F.col("quality_rank") + 1)
            + (F.col("_farm_count") - F.col("energy_rank") + 1)
        )
        ranked = ranked.withColumn("composite_score", points.cast("double"))
        ranked = ranked.withColumn(
            "composite_rank",
            F.rank().over(by_day.orderBy(F.col("composite_score").desc())),
        )

        target = ranked.select(
            "metric_date",
            "date_key",
            "farm_key",
            "farm_id",
            F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.col("premium_yield_share").cast("double").alias("premium_yield_share"),
            F.col("energy_efficiency_kwh_per_kg").cast("double").alias("energy_efficiency_kwh_per_kg"),
            F.col("yield_rank").cast("int").alias("yield_rank"),
            F.col("quality_rank").cast("int").alias("quality_rank"),
            F.col("energy_rank").cast("int").alias("energy_rank"),
            "composite_score",
            F.col("composite_rank").cast("int").alias("composite_rank"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
