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

JOB_NAME = "load_dim_farm"
TARGET_TABLE = "dim_farm"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        farms_path = f"{settings.postgres_raw_root}/farms/"

        infrastructure_path = f"{settings.postgres_raw_root}/farm_infrastructure_types/"

        growing_system_path = f"{settings.postgres_raw_root}/growing_system_types/"

        # Read all farm batches and keep the latest row for each farm.
        farms = latest_rows(
            read_full_table(
                spark,
                farms_path,
            )
        ).select(
            F.col("id").cast("long").alias("farm_id"),
            F.trim(F.col("name")).alias("name"),
            F.trim(F.col("city")).alias("city"),
            F.col("size_m2").cast("decimal(10,3)").alias("size_m2"),
            F.col("growing_beds_count").cast("long").alias("growing_beds_count"),
            F.col("status").alias("status"),
            F.col("infrastructure_type_id")
            .cast("long")
            .alias("infrastructure_type_id"),
            F.col("growing_system_type_id")
            .cast("long")
            .alias("growing_system_type_id"),
        )

        # Read all infrastructure type batches and keep the latest rows.
        infrastructure_types = latest_rows(
            read_full_table(
                spark,
                infrastructure_path,
            )
        ).select(
            F.col("id").cast("long").alias("infrastructure_type_id"),
            F.trim(F.col("name")).alias("infrastructure_type_name"),
        )

        # Read all growing system type batches and keep the latest rows.
        growing_system_types = latest_rows(
            read_full_table(
                spark,
                growing_system_path,
            )
        ).select(
            F.col("id").cast("long").alias("growing_system_type_id"),
            F.trim(F.col("name")).alias("growing_system_type_name"),
        )

        # Build the current source snapshot.
        source_farms = (
            farms.join(
                F.broadcast(infrastructure_types),
                on="infrastructure_type_id",
                how="inner",
            )
            .join(
                F.broadcast(growing_system_types),
                on="growing_system_type_id",
                how="inner",
            )
            .select(
                "farm_id",
                "name",
                "city",
                "size_m2",
                "growing_beds_count",
                "status",
                "infrastructure_type_id",
                "infrastructure_type_name",
                "growing_system_type_id",
                "growing_system_type_name",
            )
        )

        # Read the current open version of each farm.
        current_farms = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                name,
                city,
                size_m2,
                growing_beds_count,
                status,
                infrastructure_type_id,
                infrastructure_type_name,
                growing_system_type_id,
                growing_system_type_name,
                valid_from
            FROM {settings.clickhouse_database}.{TARGET_TABLE} FINAL
            WHERE is_current = 1
            """,
        )

        # An empty target table indicates the initial load.
        initial_load = current_farms.isEmpty()

        comparison = source_farms.alias("source").join(
            current_farms.alias("current"),
            F.col("source.farm_id") == F.col("current.farm_id"),
            how="left",
        )

        # Compare all attributes tracked by the SCD Type 2 dimension.
        same_values = (
            F.col("source.name").eqNullSafe(F.col("current.name"))
            & F.col("source.city").eqNullSafe(F.col("current.city"))
            & F.col("source.size_m2").eqNullSafe(F.col("current.size_m2"))
            & F.col("source.growing_beds_count").eqNullSafe(
                F.col("current.growing_beds_count")
            )
            & F.col("source.status").eqNullSafe(F.col("current.status"))
            & F.col("source.infrastructure_type_id").eqNullSafe(
                F.col("current.infrastructure_type_id")
            )
            & F.col("source.infrastructure_type_name").eqNullSafe(
                F.col("current.infrastructure_type_name")
            )
            & F.col("source.growing_system_type_id").eqNullSafe(
                F.col("current.growing_system_type_id")
            )
            & F.col("source.growing_system_type_name").eqNullSafe(
                F.col("current.growing_system_type_name")
            )
        )

        # Keep only new farms and farms whose attributes changed.
        changes = comparison.filter(F.col("current.farm_id").isNull() | (~same_values))

        if changes.isEmpty():
            LOGGER.info("No changes for dim_farm.")
            return

        load_time = datetime.now(timezone.utc).replace(tzinfo=None)

        run_version = time.time_ns()

        new_valid_from = INITIAL_VALID_FROM if initial_load else load_time

        # Select the new source values for affected farms.
        changed_source_farms = changes.select(
            F.col("source.farm_id").alias("farm_id"),
            F.col("source.name").alias("name"),
            F.col("source.city").alias("city"),
            F.col("source.size_m2").alias("size_m2"),
            F.col("source.growing_beds_count").alias("growing_beds_count"),
            F.col("source.status").alias("status"),
            F.col("source.infrastructure_type_id").alias("infrastructure_type_id"),
            F.col("source.infrastructure_type_name").alias("infrastructure_type_name"),
            F.col("source.growing_system_type_id").alias("growing_system_type_id"),
            F.col("source.growing_system_type_name").alias("growing_system_type_name"),
        )

        # Select current versions that must be closed.
        existing_changes = changes.filter(F.col("current.farm_id").isNotNull()).select(
            F.col("current.farm_id").alias("farm_id"),
            F.col("current.name").alias("name"),
            F.col("current.city").alias("city"),
            F.col("current.size_m2").alias("size_m2"),
            F.col("current.growing_beds_count").alias("growing_beds_count"),
            F.col("current.status").alias("status"),
            F.col("current.infrastructure_type_id").alias("infrastructure_type_id"),
            F.col("current.infrastructure_type_name").alias("infrastructure_type_name"),
            F.col("current.growing_system_type_id").alias("growing_system_type_id"),
            F.col("current.growing_system_type_name").alias("growing_system_type_name"),
            F.col("current.valid_from").alias("valid_from"),
        )

        # Close the previous version of each changed existing farm.
        closed_versions = existing_changes.select(
            "farm_id",
            "name",
            "city",
            "size_m2",
            "growing_beds_count",
            "status",
            "infrastructure_type_id",
            "infrastructure_type_name",
            "growing_system_type_id",
            "growing_system_type_name",
            "valid_from",
            F.lit(load_time).cast("timestamp").alias("valid_to"),
            F.lit(0).cast("byte").alias("is_current"),
            F.lit(run_version).cast("long").alias("_version"),
        )

        # Create the new current version of each new or changed farm.
        new_versions = changed_source_farms.select(
            "farm_id",
            "name",
            "city",
            "size_m2",
            "growing_beds_count",
            "status",
            "infrastructure_type_id",
            "infrastructure_type_name",
            "growing_system_type_id",
            "growing_system_type_name",
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
