import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_farm_leaderboard"
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

        # Calculate daily ranks directly in ClickHouse.
        leaderboard = read_clickhouse_query(
            spark,
            settings,
            f"""
            WITH base AS
            (
                SELECT
                    metric_date,
                    farm_key,
                    farm_id,
                    total_yield_kg,
                    if(
                        total_yield_kg > 0,
                        toFloat64(premium_yield_kg)
                            / toFloat64(total_yield_kg),
                        0.0
                    ) AS premium_yield_share,
                    if(
                        total_yield_kg > 0
                        AND energy_kwh > 0,
                        energy_kwh / toFloat64(total_yield_kg),
                        0.0
                    ) AS energy_efficiency_kwh_per_kg
                FROM
                    {settings.clickhouse_database}.fact_daily_farm_metrics
                    FINAL
                WHERE metric_date >= today() - {refresh_offset}
                  AND total_yield_kg > 0
            ),
            ranked AS
            (
                SELECT
                    *,
                    dense_rank() OVER (
                        PARTITION BY metric_date
                        ORDER BY total_yield_kg DESC
                    ) AS yield_rank,
                    dense_rank() OVER (
                        PARTITION BY metric_date
                        ORDER BY premium_yield_share DESC
                    ) AS quality_rank,
                    dense_rank() OVER (
                        PARTITION BY metric_date
                        ORDER BY
                            if(
                                energy_efficiency_kwh_per_kg > 0,
                                energy_efficiency_kwh_per_kg,
                                1e308
                            ) ASC
                    ) AS energy_rank,
                    count() OVER (
                        PARTITION BY metric_date
                    ) AS farm_count
                FROM base
            ),
            scored AS
            (
                SELECT
                    *,
                    (
                        100.0 * (
                            1.0
                            - toFloat64(yield_rank - 1)
                            / greatest(
                                toFloat64(farm_count - 1),
                                1.0
                            )
                        )
                        +
                        100.0 * (
                            1.0
                            - toFloat64(quality_rank - 1)
                            / greatest(
                                toFloat64(farm_count - 1),
                                1.0
                            )
                        )
                        +
                        100.0 * (
                            1.0
                            - toFloat64(energy_rank - 1)
                            / greatest(
                                toFloat64(farm_count - 1),
                                1.0
                            )
                        )
                    ) / 3.0 AS composite_score
                FROM ranked
            )
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
                dense_rank() OVER (
                    PARTITION BY metric_date
                    ORDER BY composite_score DESC
                ) AS composite_rank
            FROM scored
            """,
        )

        if leaderboard.isEmpty():
            LOGGER.info(
                "No leaderboard data found for the last %s days.",
                REFRESH_DAYS,
            )
            return

        output = leaderboard.select(
            F.col("metric_date").cast("date").alias("metric_date"),
            F.date_format(F.col("metric_date"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.col("farm_key").cast("decimal(20,0)").alias("farm_key"),
            F.col("farm_id").cast("decimal(20,0)").alias("farm_id"),
            F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.col("premium_yield_share").cast("double").alias("premium_yield_share"),
            F.col("energy_efficiency_kwh_per_kg")
            .cast("double")
            .alias("energy_efficiency_kwh_per_kg"),
            F.col("yield_rank").cast("int").alias("yield_rank"),
            F.col("quality_rank").cast("int").alias("quality_rank"),
            F.col("energy_rank").cast("int").alias("energy_rank"),
            F.col("composite_score").cast("double").alias("composite_score"),
            F.col("composite_rank").cast("int").alias("composite_rank"),
            F.current_timestamp().alias("_loaded_at"),
        )

        write_clickhouse_table(output, settings, TARGET_TABLE)

        LOGGER.info(f"{TARGET_TABLE} refreshed for the last {REFRESH_DAYS} days.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
