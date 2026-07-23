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

JOB_NAME = "load_dim_user_farm_role"
TARGET_TABLE = "dim_user_farm_role"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        # Read the current source state of each assignment.
        user_roles = latest_rows(
            read_full_table(
                spark,
                f"{settings.postgres_raw_root}/user_roles/",
            )
        ).select(
            F.col("id").cast("long").alias("user_role_id"),
            F.col("user_id").cast("long"),
            F.col("role_id").cast("long"),
            F.col("farm_id").cast("long"),
        )

        # Read the current source state of each user.
        users = latest_rows(
            read_full_table(
                spark,
                f"{settings.postgres_raw_root}/users/",
            )
        ).select(
            F.col("id").cast("long").alias("user_id"),
            F.trim(F.col("full_name")).alias("user_full_name"),
        )

        # Read the current source state of each role.
        roles = latest_rows(
            read_full_table(
                spark,
                f"{settings.postgres_raw_root}/roles/",
            )
        ).select(
            F.col("id").cast("long").alias("role_id"),
            F.trim(F.col("name")).alias("role_name"),
        )

        # Read the current farm surrogate keys.
        farms = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                farm_key,
                name AS farm_name
            FROM {settings.clickhouse_database}.dim_farm FINAL
            WHERE is_current = 1
            """,
        )

        if farms.isEmpty():
            LOGGER.warning(
                "Skipping dim_user_farm_role load: dim_farm has no current rows. "
                "Load dim_farm first."
            )
            return

        # Build the current source snapshot.
        source_user_roles = (
            user_roles.join(F.broadcast(users), on="user_id", how="inner")
            .join(F.broadcast(roles), on="role_id", how="inner")
            .join(F.broadcast(farms), on="farm_id", how="left")
            .select(
                "user_role_id",
                "user_id",
                "role_id",
                F.when(F.col("farm_id").isNull(), F.lit(0))
                .otherwise(F.col("farm_key"))
                .alias("farm_key"),
                F.coalesce(F.col("farm_id"), F.lit(0)).alias("farm_id"),
                "user_full_name",
                "role_name",
                F.when(F.col("farm_id").isNull(), F.lit(""))
                .otherwise(F.col("farm_name"))
                .alias("farm_name"),
            )
        )

        # Read the current open version of each assignment.
        current_user_roles = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                user_role_id,
                user_id,
                role_id,
                farm_key,
                farm_id,
                user_full_name,
                role_name,
                farm_name,
                valid_from
            FROM {settings.clickhouse_database}.{TARGET_TABLE} FINAL
            WHERE is_current = 1
            """,
        )

        # An empty target table indicates the initial load.
        initial_load = current_user_roles.isEmpty()

        comparison = source_user_roles.alias("source").join(
            current_user_roles.alias("current"),
            F.col("source.user_role_id") == F.col("current.user_role_id"),
            how="left",
        )

        same_values = (
            F.col("source.user_id").eqNullSafe(F.col("current.user_id"))
            & F.col("source.role_id").eqNullSafe(F.col("current.role_id"))
            & F.col("source.farm_key").eqNullSafe(F.col("current.farm_key"))
            & F.col("source.farm_id").eqNullSafe(F.col("current.farm_id"))
            & F.col("source.user_full_name").eqNullSafe(F.col("current.user_full_name"))
            & F.col("source.role_name").eqNullSafe(F.col("current.role_name"))
            & F.col("source.farm_name").eqNullSafe(F.col("current.farm_name"))
        )

        # Keep only new or changed assignments.
        changes = comparison.filter(
            F.col("current.user_role_id").isNull() | (~same_values)
        )

        if changes.isEmpty():
            LOGGER.info("No changes for dim_user_farm_role.")
            return

        load_time = datetime.now(timezone.utc).replace(tzinfo=None)

        run_version = time.time_ns()

        new_valid_from = INITIAL_VALID_FROM if initial_load else load_time

        # Close the previous version of each changed assignment.
        closed_versions = changes.filter(
            F.col("current.user_role_id").isNotNull()
        ).select(
            F.col("current.user_role_id").alias("user_role_id"),
            F.col("current.user_id").alias("user_id"),
            F.col("current.role_id").alias("role_id"),
            F.col("current.farm_key").alias("farm_key"),
            F.col("current.farm_id").alias("farm_id"),
            F.col("current.user_full_name").alias("user_full_name"),
            F.col("current.role_name").alias("role_name"),
            F.col("current.farm_name").alias("farm_name"),
            F.col("current.valid_from").alias("valid_from"),
            F.lit(load_time).cast("timestamp").alias("valid_to"),
            F.lit(0).cast("byte").alias("is_current"),
            F.lit(run_version).cast("long").alias("_version"),
        )

        # Create the new current version of each assignment.
        new_versions = changes.select(
            F.col("source.user_role_id").alias("user_role_id"),
            F.col("source.user_id").alias("user_id"),
            F.col("source.role_id").alias("role_id"),
            F.col("source.farm_key").alias("farm_key"),
            F.col("source.farm_id").alias("farm_id"),
            F.col("source.user_full_name").alias("user_full_name"),
            F.col("source.role_name").alias("role_name"),
            F.col("source.farm_name").alias("farm_name"),
            F.lit(new_valid_from).cast("timestamp").alias("valid_from"),
            F.lit(MAX_VALID_TO).cast("timestamp").alias("valid_to"),
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
