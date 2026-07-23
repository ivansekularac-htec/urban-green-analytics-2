import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_daily_farm_metrics"
TARGET_TABLE = "fact_daily_farm_metrics"

REFRESH_DAYS = 365

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

        # Read harvests from the refresh window.
        harvests = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                farm_key,
                quality_grade_id,
                harvest_date AS metric_date,
                weight_kg
            FROM {settings.clickhouse_database}.fact_harvests FINAL
            WHERE harvest_date >= today() - {refresh_offset}
            """,
        )

        # Read sensor readings from the refresh window.
        sensor_readings = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                farm_key,
                sensor_type_key,
                reading_date AS metric_date,
                reading_ts,
                value,
                is_anomaly
            FROM {settings.clickhouse_database}.fact_sensor_readings FINAL
            WHERE reading_date >= today() - {refresh_offset}
            """,
        )

        quality_grades = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                quality_grade_id,
                is_premium
            FROM {settings.clickhouse_database}.dim_quality_grade FINAL
            """,
        )

        sensor_types = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_type_key,
                name AS sensor_type_name
            FROM {settings.clickhouse_database}.dim_sensor_type FINAL
            """,
        )

        # Calculate daily harvest metrics.
        harvest_metrics = (
            harvests.join(quality_grades, on="quality_grade_id", how="left")
            .groupBy("farm_id", "metric_date")
            .agg(
                F.max("farm_key").alias("harvest_farm_key"),
                F.sum("weight_kg").alias("total_yield_kg"),
                F.count("*").alias("harvest_count"),
                F.sum(
                    F.when(F.col("is_premium") == 1, F.col("weight_kg")).otherwise(
                        F.lit(0)
                    )
                ).alias("premium_yield_kg"),
            )
        )

        # Calculate daily sensor and energy metrics.
        sensor_metrics = (
            sensor_readings.join(sensor_types, on="sensor_type_key", how="left")
            .groupBy(
                "farm_id",
                "metric_date",
            )
            .agg(
                F.max("farm_key").alias("sensor_farm_key"),
                F.sum(
                    F.when(
                        F.col("sensor_type_name") == "Energy Usage", F.col("value")
                    ).otherwise(F.lit(0.0))
                ).alias("energy_kwh"),
                F.count("*").alias("reading_count"),
                F.sum("is_anomaly").alias("anomaly_count"),
                F.max("reading_ts").alias("last_sensor_reading_ts"),
            )
        )

        # Combine harvest and sensor metrics for each farm and date.
        metrics = harvest_metrics.join(
            sensor_metrics,
            on=[
                "farm_id",
                "metric_date",
            ],
            how="full",
        )

        output = metrics.select(
            F.col("metric_date"),
            F.date_format(F.col("metric_date"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.coalesce(F.col("harvest_farm_key"), F.col("sensor_farm_key")).alias(
                "farm_key"
            ),
            F.col("farm_id").cast("long").alias("farm_id"),
            (F.year("metric_date") * F.lit(100) + F.weekofyear("metric_date"))
            .cast("int")
            .alias("year_week"),
            F.coalesce(F.col("total_yield_kg"), F.lit(0))
            .cast("decimal(18,3)")
            .alias("total_yield_kg"),
            F.coalesce(F.col("harvest_count"), F.lit(0))
            .cast("long")
            .alias("harvest_count"),
            F.coalesce(F.col("premium_yield_kg"), F.lit(0))
            .cast("decimal(18,3)")
            .alias("premium_yield_kg"),
            (
                F.coalesce(F.col("total_yield_kg"), F.lit(0))
                - F.coalesce(F.col("premium_yield_kg"), F.lit(0))
            )
            .cast("decimal(18,3)")
            .alias("non_premium_yield_kg"),
            F.coalesce(F.col("energy_kwh"), F.lit(0.0))
            .cast("double")
            .alias("energy_kwh"),
            F.coalesce(F.col("reading_count"), F.lit(0))
            .cast("long")
            .alias("reading_count"),
            F.coalesce(F.col("anomaly_count"), F.lit(0))
            .cast("long")
            .alias("anomaly_count"),
            (
                F.coalesce(F.col("reading_count"), F.lit(0))
                - F.coalesce(F.col("anomaly_count"), F.lit(0))
            )
            .cast("long")
            .alias("in_range_count"),
            F.col("last_sensor_reading_ts"),
            F.current_timestamp().alias("_loaded_at"),
        )

        write_clickhouse_table(
            output,
            settings,
            TARGET_TABLE,
        )

        LOGGER.info(f"{TARGET_TABLE} refreshed for the last {REFRESH_DAYS} days.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
