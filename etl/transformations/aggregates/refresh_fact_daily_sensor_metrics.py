import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_daily_sensor_metrics"
TARGET_TABLE = "fact_daily_sensor_metrics"

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

        # Aggregate in ClickHouse to avoid transferring raw readings to Spark.
        sensor_metrics = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                reading_date AS metric_date,
                farm_id,
                max(farm_key) AS farm_key,
                sensor_type_key,
                count() AS reading_count,
                sum(value) AS sum_value,
                min(value) AS min_value,
                max(value) AS max_value,
                countIf(is_anomaly = 1) AS anomaly_count,
                countIf(is_anomaly = 0) AS in_range_count
            FROM {settings.clickhouse_database}.fact_sensor_readings FINAL
            WHERE reading_date >= today() - {refresh_offset}
            GROUP BY
                reading_date,
                farm_id,
                sensor_type_key
            """,
        )

        output = sensor_metrics.select(
            F.col("metric_date").cast("date").alias("metric_date"),
            F.date_format(F.col("metric_date"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.col("farm_key").cast("decimal(20,0)").alias("farm_key"),
            F.col("farm_id").cast("decimal(20,0)").alias("farm_id"),
            F.col("sensor_type_key").cast("decimal(20,0)").alias("sensor_type_key"),
            F.col("reading_count").cast("decimal(20,0)").alias("reading_count"),
            F.col("sum_value").cast("double").alias("sum_value"),
            F.col("min_value").cast("double").alias("min_value"),
            F.col("max_value").cast("double").alias("max_value"),
            F.col("anomaly_count").cast("decimal(20,0)").alias("anomaly_count"),
            F.col("in_range_count").cast("decimal(20,0)").alias("in_range_count"),
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
