import logging
import time
from datetime import datetime, timezone

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import (
    INITIAL_VALID_FROM,
    MAX_VALID_TO,
    WarehouseSettings,
)
from common.minio import latest_rows, read_full_table
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_dim_sensor"
TARGET_TABLE = "dim_sensor"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        sensors_path = f"{settings.postgres_raw_root}/sensors/"

        # Read the current source state of each sensor.
        sensors = latest_rows(
            read_full_table(
                spark,
                sensors_path,
            )
        ).select(
            F.col("id").cast("long").alias("sensor_id"),
            F.col("farm_id").cast("long").alias("farm_id"),
            F.col("sensor_type_id").cast("long").alias("sensor_type_id"),
            F.trim(F.col("serial_number")).alias("serial_number"),
            F.trim(F.col("status")).alias("status"),
            F.from_unixtime(F.col("installed_at"))
            .cast("timestamp")
            .alias("installed_at"),
        )

        # Read the current parent dimension keys.
        current_farms = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                farm_key
            FROM {settings.clickhouse_database}.dim_farm FINAL
            WHERE is_current = 1
            """,
        )

        if current_farms.isEmpty():
            LOGGER.warning(
                "Skipping dim_sensor load: dim_farm has no current rows. "
                "Load dim_farm first."
            )
            return

        current_sensor_types = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_type_id,
                sensor_type_key
            FROM {settings.clickhouse_database}.dim_sensor_type FINAL
            WHERE is_current = 1
            """,
        )

        if current_sensor_types.isEmpty():
            LOGGER.warning(
                "Skipping dim_sensor load: dim_sensor_type has no current rows. "
                "Load dim_sensor_type first."
            )
            return

        # Resolve the current parent surrogate keys.
        source_sensors = (
            sensors.join(
                F.broadcast(current_farms),
                on="farm_id",
                how="inner",
            )
            .join(
                F.broadcast(current_sensor_types),
                on="sensor_type_id",
                how="inner",
            )
            .select(
                "sensor_id",
                "farm_key",
                "sensor_type_key",
                "serial_number",
                "status",
                "installed_at",
            )
        )

        # Read the current open sensor versions.
        current_sensors = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_id,
                farm_key,
                sensor_type_key,
                serial_number,
                status,
                installed_at,
                valid_from
            FROM {settings.clickhouse_database}.{TARGET_TABLE} FINAL
            WHERE is_current = 1
            """,
        )

        # An empty target table indicates the initial load.
        initial_load = current_sensors.isEmpty()

        comparison = source_sensors.alias("source").join(
            current_sensors.alias("current"),
            F.col("source.sensor_id") == F.col("current.sensor_id"),
            how="left",
        )

        same_values = (
            F.col("source.farm_key").eqNullSafe(F.col("current.farm_key"))
            & F.col("source.sensor_type_key").eqNullSafe(
                F.col("current.sensor_type_key")
            )
            & F.col("source.serial_number").eqNullSafe(F.col("current.serial_number"))
            & F.col("source.status").eqNullSafe(F.col("current.status"))
            & F.col("source.installed_at").eqNullSafe(F.col("current.installed_at"))
        )

        # Keep only new or changed sensors.
        changes = comparison.filter(
            F.col("current.sensor_id").isNull() | (~same_values)
        )

        if changes.isEmpty():
            LOGGER.info("No changes for dim_sensor.")
            return

        load_time = datetime.now(timezone.utc).replace(tzinfo=None)

        run_version = time.time_ns()

        new_valid_from = INITIAL_VALID_FROM if initial_load else load_time

        # Close the previous version of each changed sensor.
        closed_versions = changes.filter(F.col("current.sensor_id").isNotNull()).select(
            F.col("current.sensor_id").alias("sensor_id"),
            F.col("current.farm_key").alias("farm_key"),
            F.col("current.sensor_type_key").alias("sensor_type_key"),
            F.col("current.serial_number").alias("serial_number"),
            F.col("current.status").alias("status"),
            F.col("current.installed_at").alias("installed_at"),
            F.col("current.valid_from").alias("valid_from"),
            F.lit(load_time).cast("timestamp").alias("valid_to"),
            F.lit(0).cast("byte").alias("is_current"),
            F.lit(run_version).cast("long").alias("_version"),
        )

        # Create the new current version of each new or changed sensor.
        new_versions = changes.select(
            F.col("source.sensor_id").alias("sensor_id"),
            F.col("source.farm_key").alias("farm_key"),
            F.col("source.sensor_type_key").alias("sensor_type_key"),
            F.col("source.serial_number").alias("serial_number"),
            F.col("source.status").alias("status"),
            F.col("source.installed_at").alias("installed_at"),
            F.lit(new_valid_from).cast("timestamp").alias("valid_from"),
            F.to_timestamp(F.lit(MAX_VALID_TO)).alias("valid_to"),
            F.lit(1).cast("byte").alias("is_current"),
            F.lit(run_version).cast("long").alias("_version"),
        )

        output = closed_versions.unionByName(new_versions)

        write_clickhouse_table(
            output,
            settings,
            TARGET_TABLE,
        )

        LOGGER.info(f"{TARGET_TABLE} loaded successfully.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
