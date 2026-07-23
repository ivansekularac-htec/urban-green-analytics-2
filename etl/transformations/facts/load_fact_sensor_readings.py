import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.load_state import read_cursor, save_cursor
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_sensor_readings"
TARGET_TABLE = "fact_sensor_readings"
CURSOR_KEY = "event_date"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        cursor = read_cursor(spark, settings, JOB_NAME)

        readings_path = f"{settings.kafka_raw_root}/sensor_readings/"

        last_timestamp = cursor.get(CURSOR_KEY, 0)

        # Read all historical sensor versions.
        sensor_versions = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_id,
                farm_key,
                sensor_type_key,
                valid_from,
                valid_to
            FROM {settings.clickhouse_database}.dim_sensor FINAL
            """,
        )

        if sensor_versions.isEmpty():
            LOGGER.warning(
                "Skipping fact_sensor_readings load: dim_sensor contains "
                "no rows. Load dim_sensor first. Cursor was not advanced."
            )
            return

        # Read the optimal range of each sensor type version.
        sensor_types = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_type_key,
                optimal_min,
                optimal_max
            FROM {settings.clickhouse_database}.dim_sensor_type FINAL
            """,
        )

        if sensor_types.isEmpty():
            LOGGER.warning(
                "Skipping fact_sensor_readings load: dim_sensor_type "
                "contains no rows. Load dim_sensor_type first. "
                "Cursor was not advanced."
            )
            return

        # Read the Kafka landing table and reprocess the last timestamp.
        readings = (
            spark.read.parquet(readings_path)
            .filter(F.col("timestamp") >= F.lit(last_timestamp))
            .select(
                F.col("farm_sensor_id").cast("long").alias("sensor_id"),
                F.col("farm_id").cast("long").alias("farm_id"),
                F.col("value").cast("double").alias("value"),
                F.col("timestamp").cast("long").alias("source_timestamp"),
                F.from_unixtime(F.col("timestamp"))
                .cast("timestamp")
                .alias("reading_ts"),
                F.col("event_date").cast("date").alias("reading_date"),
            )
        )

        max_timestamp = readings.agg(
            F.max("source_timestamp").alias("max_timestamp")
        ).first()["max_timestamp"]

        if max_timestamp is None:
            LOGGER.info("No new data for fact_sensor_readings.")
            return

        reading = readings.alias("reading")
        sensor = sensor_versions.alias("sensor")

        # Resolve the sensor version valid at reading time.
        matched_readings = reading.join(
            sensor,
            (F.col("reading.sensor_id") == F.col("sensor.sensor_id"))
            & (F.col("reading.reading_ts") >= F.col("sensor.valid_from"))
            & (F.col("reading.reading_ts") < F.col("sensor.valid_to")),
            how="left",
        ).join(
            F.broadcast(sensor_types.alias("sensor_type")),
            F.col("sensor.sensor_type_key") == F.col("sensor_type.sensor_type_key"),
            how="left",
        )

        # Stop the load if a historical dimension key is missing.
        missing_dimension = (
            matched_readings.filter(
                F.col("sensor.sensor_id").isNull()
                | F.col("sensor_type.sensor_type_key").isNull()
            )
            .limit(1)
            .count()
        )

        if missing_dimension:
            raise ValueError(
                "Some sensor readings could not be matched to their dimension versions."
            )

        output = matched_readings.select(
            # Stable key for one sensor reading.
            (
                F.col("reading.source_timestamp") * F.lit(1_000_000)
                + F.col("reading.sensor_id")
            )
            .cast("long")
            .alias("reading_key"),
            F.col("sensor.farm_key").alias("farm_key"),
            F.col("reading.farm_id").alias("farm_id"),
            # The target schema defines sensor_key as farm_sensor_id.
            F.col("reading.sensor_id").alias("sensor_key"),
            F.col("sensor.sensor_type_key").alias("sensor_type_key"),
            F.date_format(F.col("reading.reading_ts"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.date_format(F.col("reading.reading_ts"), "HHmmss")
            .cast("int")
            .alias("time_key"),
            F.col("reading.reading_ts").alias("reading_ts"),
            F.col("reading.reading_date").alias("reading_date"),
            F.col("reading.value").alias("value"),
            F.when(
                (F.col("reading.value") < F.col("sensor_type.optimal_min"))
                | (F.col("reading.value") > F.col("sensor_type.optimal_max")),
                F.lit(1),
            )
            .otherwise(F.lit(0))
            .cast("byte")
            .alias("is_anomaly"),
            F.current_timestamp().alias("_loaded_at"),
        )

        write_clickhouse_table(
            output,
            settings,
            TARGET_TABLE,
        )

        # Advance the cursor only after the target write succeeds.
        save_cursor(
            spark,
            settings,
            JOB_NAME,
            {
                CURSOR_KEY: int(max_timestamp),
            },
        )

        LOGGER.info(f"{TARGET_TABLE} loaded successfully.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
