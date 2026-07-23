import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.spark_session import create_spark_session
from pyspark.sql import Window
from pyspark.sql import functions as F

JOB_NAME = "refresh_fact_farm_leaderboard"
TARGET_TABLE = "fact_farm_leaderboard"

REFRESH_DAYS = 30

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        refresh_offset = REFRESH_DAYS - 1

        # Read only the required source rows and columns.
        metrics = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                metric_date,
                farm_key,
                farm_id,
                total_yield_kg,
                premium_yield_kg,
                energy_kwh
            FROM {settings.clickhouse_database}.fact_daily_farm_metrics FINAL
            WHERE metric_date >= today() - {refresh_offset}
              AND total_yield_kg > 0
            """,
        )

        # Calculate leaderboard KPI values.
        base = metrics.select(
            "metric_date",
            "farm_key",
            "farm_id",
            "total_yield_kg",
            (
                F.col("premium_yield_kg").cast("double")
                / F.col("total_yield_kg").cast("double")
            ).alias("premium_yield_share"),
            F.when(
                F.col("energy_kwh") > 0,
                F.col("energy_kwh").cast("double")
                / F.col("total_yield_kg").cast("double"),
            )
            .otherwise(F.lit(0.0))
            .alias("energy_efficiency_kwh_per_kg"),
        )

        yield_window = Window.partitionBy("metric_date").orderBy(
            F.col("total_yield_kg").desc()
        )

        quality_window = Window.partitionBy("metric_date").orderBy(
            F.col("premium_yield_share").desc()
        )

        energy_window = Window.partitionBy("metric_date").orderBy(
            F.when(
                F.col("energy_efficiency_kwh_per_kg") > 0,
                F.col("energy_efficiency_kwh_per_kg"),
            ).asc_nulls_last()
        )

        farm_count_window = Window.partitionBy("metric_date")

        # Calculate ranks and the number of ranked farms per day.
        ranked = base.select(
            "metric_date",
            "farm_key",
            "farm_id",
            "total_yield_kg",
            "premium_yield_share",
            "energy_efficiency_kwh_per_kg",
            F.dense_rank().over(yield_window).alias("yield_rank"),
            F.dense_rank().over(quality_window).alias("quality_rank"),
            F.dense_rank().over(energy_window).alias("energy_rank"),
            F.count(F.lit(1)).over(farm_count_window).alias("farm_count"),
        )

        rank_denominator = F.greatest(
            (F.col("farm_count") - F.lit(1)).cast("double"),
            F.lit(1.0),
        )

        # Calculate normalized scores using the same dense-rank logic.
        scored = ranked.select(
            "metric_date",
            "farm_key",
            "farm_id",
            "total_yield_kg",
            "premium_yield_share",
            "energy_efficiency_kwh_per_kg",
            "yield_rank",
            "quality_rank",
            "energy_rank",
            (
                F.lit(100.0)
                * (
                    F.lit(1.0)
                    - (F.col("yield_rank") - F.lit(1)).cast("double") / rank_denominator
                )
            ).alias("yield_score"),
            (
                F.lit(100.0)
                * (
                    F.lit(1.0)
                    - (F.col("quality_rank") - F.lit(1)).cast("double")
                    / rank_denominator
                )
            ).alias("quality_score"),
            F.when(
                F.col("energy_efficiency_kwh_per_kg") > 0,
                F.lit(100.0)
                * (
                    F.lit(1.0)
                    - (F.col("energy_rank") - F.lit(1)).cast("double")
                    / rank_denominator
                ),
            )
            .otherwise(F.lit(0.0))
            .alias("energy_score"),
        )

        leaderboard_scores = scored.select(
            "metric_date",
            "farm_key",
            "farm_id",
            "total_yield_kg",
            "premium_yield_share",
            "energy_efficiency_kwh_per_kg",
            "yield_rank",
            "quality_rank",
            "energy_rank",
            F.round(
                (F.col("yield_score") + F.col("quality_score") + F.col("energy_score"))
                / F.lit(3.0),
                6,
            ).alias("composite_score"),
        )

        composite_window = Window.partitionBy("metric_date").orderBy(
            F.col("composite_score").desc()
        )

        # Build the calculated leaderboard snapshot.
        calculated_leaderboard = leaderboard_scores.select(
            F.col("metric_date").cast("date").alias("metric_date"),
            F.date_format(
                F.col("metric_date"),
                "yyyyMMdd",
            )
            .cast("int")
            .alias("date_key"),
            F.col("farm_key").cast("decimal(20,0)").alias("farm_key"),
            F.col("farm_id").cast("decimal(20,0)").alias("farm_id"),
            F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.round(
                F.col("premium_yield_share"),
                6,
            )
            .cast("double")
            .alias("premium_yield_share"),
            F.round(
                F.col("energy_efficiency_kwh_per_kg"),
                6,
            )
            .cast("double")
            .alias("energy_efficiency_kwh_per_kg"),
            F.col("yield_rank").cast("int").alias("yield_rank"),
            F.col("quality_rank").cast("int").alias("quality_rank"),
            F.col("energy_rank").cast("int").alias("energy_rank"),
            F.col("composite_score").cast("double").alias("composite_score"),
            F.dense_rank().over(composite_window).cast("int").alias("composite_rank"),
        )

        # Read the current logical target state.
        current_leaderboard = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                metric_date,
                farm_key,
                farm_id,
                total_yield_kg,
                premium_yield_share,
                energy_efficiency_kwh_per_kg,
                yield_rank,
                quality_rank,
                energy_rank,
                composite_score,
                composite_rank
            FROM {settings.clickhouse_database}.{TARGET_TABLE} FINAL
            WHERE metric_date >= today() - {refresh_offset}
            """,
        ).select(
            F.col("metric_date").cast("date").alias("metric_date"),
            F.col("farm_key").cast("decimal(20,0)").alias("farm_key"),
            F.col("farm_id").cast("decimal(20,0)").alias("farm_id"),
            F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.round(
                F.col("premium_yield_share"),
                6,
            )
            .cast("double")
            .alias("premium_yield_share"),
            F.round(
                F.col("energy_efficiency_kwh_per_kg"),
                6,
            )
            .cast("double")
            .alias("energy_efficiency_kwh_per_kg"),
            F.col("yield_rank").cast("int").alias("yield_rank"),
            F.col("quality_rank").cast("int").alias("quality_rank"),
            F.col("energy_rank").cast("int").alias("energy_rank"),
            F.round(
                F.col("composite_score"),
                6,
            )
            .cast("double")
            .alias("composite_score"),
            F.col("composite_rank").cast("int").alias("composite_rank"),
        )

        comparison = calculated_leaderboard.alias("source").join(
            F.broadcast(current_leaderboard.alias("current")),
            (F.col("source.metric_date") == F.col("current.metric_date"))
            & (F.col("source.farm_id") == F.col("current.farm_id")),
            how="left",
        )

        # Compare all values that may change.
        same_values = (
            F.col("source.farm_key").eqNullSafe(F.col("current.farm_key"))
            & F.col("source.total_yield_kg").eqNullSafe(F.col("current.total_yield_kg"))
            & F.col("source.premium_yield_share").eqNullSafe(
                F.col("current.premium_yield_share")
            )
            & F.col("source.energy_efficiency_kwh_per_kg").eqNullSafe(
                F.col("current.energy_efficiency_kwh_per_kg")
            )
            & F.col("source.yield_rank").eqNullSafe(F.col("current.yield_rank"))
            & F.col("source.quality_rank").eqNullSafe(F.col("current.quality_rank"))
            & F.col("source.energy_rank").eqNullSafe(F.col("current.energy_rank"))
            & F.col("source.composite_score").eqNullSafe(
                F.col("current.composite_score")
            )
            & F.col("source.composite_rank").eqNullSafe(F.col("current.composite_rank"))
        )

        # Keep only new or changed leaderboard rows.
        changes = (
            comparison.filter(F.col("current.farm_id").isNull() | (~same_values))
            .select(
                F.col("source.metric_date").alias("metric_date"),
                F.col("source.date_key").alias("date_key"),
                F.col("source.farm_key").alias("farm_key"),
                F.col("source.farm_id").alias("farm_id"),
                F.col("source.total_yield_kg").alias("total_yield_kg"),
                F.col("source.premium_yield_share").alias("premium_yield_share"),
                F.col("source.energy_efficiency_kwh_per_kg").alias(
                    "energy_efficiency_kwh_per_kg"
                ),
                F.col("source.yield_rank").alias("yield_rank"),
                F.col("source.quality_rank").alias("quality_rank"),
                F.col("source.energy_rank").alias("energy_rank"),
                F.col("source.composite_score").alias("composite_score"),
                F.col("source.composite_rank").alias("composite_rank"),
                F.current_timestamp().alias("_loaded_at"),
            )
            .cache()
        )

        if changes.isEmpty():
            LOGGER.info(
                f"No changes for {TARGET_TABLE} in the last {REFRESH_DAYS} days."
            )
            return

        # The leaderboard is small, so one write partition is sufficient.
        write_clickhouse_table(
            changes.coalesce(1),
            settings,
            TARGET_TABLE,
        )

        LOGGER.info(
            f"{TARGET_TABLE} refreshed successfully for the last {REFRESH_DAYS} days."
        )

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
