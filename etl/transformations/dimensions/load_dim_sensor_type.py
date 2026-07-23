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

JOB_NAME = "load_dim_sensor_type"
TARGET_TABLE = "dim_sensor_type"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        sensor_types_path = f"{settings.postgres_raw_root}/sensor_types/"

        # Read all source batches and keep the latest row
        # for each sensor type.
        source_sensor_types = latest_rows(
            read_full_table(spark, sensor_types_path)
        ).select(
            F.col("id").cast("long").alias("sensor_type_id"),
            F.trim(F.col("name")).alias("name"),
            F.trim(F.col("unit")).alias("unit"),
            F.coalesce(F.trim(F.col("description")), F.lit("")).alias("description"),
            F.col("optimal_min").cast("double").alias("optimal_min"),
            F.col("optimal_max").cast("double").alias("optimal_max"),
        )

        # Read the current open version of each sensor type.
        current_sensor_types = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                sensor_type_id,
                name,
                unit,
                description,
                optimal_min,
                optimal_max,
                valid_from
            FROM {settings.clickhouse_database}.{TARGET_TABLE} FINAL
            WHERE is_current = 1
            """,
        )

        # An empty target table indicates the initial load.
        initial_load = current_sensor_types.isEmpty()

        comparison = source_sensor_types.alias("source").join(
            current_sensor_types.alias("current"),
            F.col("source.sensor_type_id") == F.col("current.sensor_type_id"),
            how="left",
        )

        # Compare all attributes tracked by the SCD Type 2 dimension.
        same_values = (
            F.col("source.name").eqNullSafe(F.col("current.name"))
            & F.col("source.unit").eqNullSafe(F.col("current.unit"))
            & F.col("source.description").eqNullSafe(F.col("current.description"))
            & F.col("source.optimal_min").eqNullSafe(F.col("current.optimal_min"))
            & F.col("source.optimal_max").eqNullSafe(F.col("current.optimal_max"))
        )

        # Keep only new or changed sensor types.
        changes = comparison.filter(
            F.col("current.sensor_type_id").isNull() | (~same_values)
        )

        if changes.isEmpty():
            LOGGER.info("No changes for dim_sensor_type.")
            return

        load_time = datetime.now(timezone.utc).replace(tzinfo=None)

        run_version = time.time_ns()

        new_valid_from = INITIAL_VALID_FROM if initial_load else load_time

        # Select the new source values.
        changed_source_rows = changes.select(
            F.col("source.sensor_type_id").alias("sensor_type_id"),
            F.col("source.name").alias("name"),
            F.col("source.unit").alias("unit"),
            F.col("source.description").alias("description"),
            F.col("source.optimal_min").alias("optimal_min"),
            F.col("source.optimal_max").alias("optimal_max"),
        )

        # Select current rows that must be closed.
        existing_changes = changes.filter(
            F.col("current.sensor_type_id").isNotNull()
        ).select(
            F.col("current.sensor_type_id").alias("sensor_type_id"),
            F.col("current.name").alias("name"),
            F.col("current.unit").alias("unit"),
            F.col("current.description").alias("description"),
            F.col("current.optimal_min").alias("optimal_min"),
            F.col("current.optimal_max").alias("optimal_max"),
            F.col("current.valid_from").alias("valid_from"),
        )

        # Close the previous version of each changed sensor type.
        closed_versions = existing_changes.select(
            "sensor_type_id",
            "name",
            "unit",
            "description",
            "optimal_min",
            "optimal_max",
            "valid_from",
            F.lit(load_time).cast("timestamp").alias("valid_to"),
            F.lit(0).cast("byte").alias("is_current"),
            F.lit(run_version).cast("long").alias("_version"),
        )

        # Create the new current version of each new or changed row.
        new_versions = changed_source_rows.select(
            "sensor_type_id",
            "name",
            "unit",
            "description",
            "optimal_min",
            "optimal_max",
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
