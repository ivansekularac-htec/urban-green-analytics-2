import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_daily_farm_quality_metrics"
TARGET_TABLE = "fact_daily_farm_quality_metrics"

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

        # Push aggregation to ClickHouse to avoid loading raw harvest rows into Spark.
        quality_metrics = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                harvest_date AS metric_date,
                farm_id,
                max(farm_key) AS farm_key,
                quality_grade_id,
                sum(weight_kg) AS total_yield_kg,
                count() AS harvest_count
            FROM {settings.clickhouse_database}.fact_harvests FINAL
            WHERE harvest_date >= today() - {refresh_offset}
            GROUP BY
                harvest_date,
                farm_id,
                quality_grade_id
            """,
        )

        output = quality_metrics.select(
            F.col("metric_date").cast("date").alias("metric_date"),
            F.date_format(F.col("metric_date"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.col("farm_key").cast("decimal(20,0)").alias("farm_key"),
            F.col("farm_id").cast("decimal(20,0)").alias("farm_id"),
            F.col("quality_grade_id").cast("decimal(20,0)").alias("quality_grade_id"),
            F.col("total_yield_kg").cast("decimal(18,3)").alias("total_yield_kg"),
            F.col("harvest_count").cast("int").alias("harvest_count"),
            F.current_timestamp().alias("_loaded_at"),
        )

        if output.isEmpty():
            LOGGER.info("No quality metrics found for the last %s days.", REFRESH_DAYS)
            return

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
