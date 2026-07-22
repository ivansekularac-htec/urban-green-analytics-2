"""
Load the dim_sensor warehouse SCD2 dimension.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from transformations.common import (
    create_spark,
    epoch_to_timestamp,
    read_clickhouse,
    read_current_snapshot,
    write_clickhouse,
)
from transformations.dimensions.scd.common import (
    add_hash,
    build_expired_version,
    build_new_version,
    split_changes,
)

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)


def transform_dim_sensor(
    sensor_df: DataFrame,
    farm_df: DataFrame,
    sensor_type_df: DataFrame,
) -> DataFrame:
    """
    Build dim_sensor warehouse shape from source snapshot.

    Converts source foreign keys:
        farm_id        -> farm_key
        sensor_type_id -> sensor_type_key

    using current warehouse dimension versions.
    """

    return (
        sensor_df.join(
            farm_df,
            sensor_df.farm_id == farm_df.farm_id,
            "left",
        )
        .join(
            sensor_type_df,
            sensor_df.sensor_type_id == sensor_type_df.sensor_type_id,
            "left",
        )
        .select(
            sensor_df.id.alias("sensor_id"),
            farm_df.farm_key,
            sensor_type_df.sensor_type_key,
            sensor_df.serial_number,
            sensor_df.status,
            epoch_to_timestamp(sensor_df.installed_at).alias("installed_at"),
        )
    )


def main():
    """
    Load dim_sensor SCD2 dimension.
    """

    spark = create_spark(
        "load_dim_sensor",
    )

    try:
        # Read the current state of all source tables.
        #
        # MinIO contains incremental batches, so this reconstructs the
        # latest PostgreSQL state by combining all batches and keeping
        # the newest record per primary key.
        sensor_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "sensors",
            primary_key="id",
        )

        # Read currently active SCD2 versions from ClickHouse.
        current_dim_farm_df = read_clickhouse(
            spark,
            """
            (
                SELECT *
                FROM dim_farm FINAL
            ) AS dim_farm
            """,
        ).filter(
            col("is_current") == 1,
        )

        current_dim_sensor_type_df = read_clickhouse(
            spark,
            """
            (
                SELECT *
                FROM dim_sensor_type FINAL
            ) AS dim_sensor_type
            """,
        ).filter(
            col("is_current") == 1,
        )

        # Prepare current dimension lookup tables.
        farm_lookup_df = current_dim_farm_df.select(
            "farm_id",
            "farm_key",
        )

        sensor_type_lookup_df = current_dim_sensor_type_df.select(
            "sensor_type_id",
            "sensor_type_key",
        )

        # Build the complete current dimension state.
        source_sensor_df = transform_dim_sensor(
            sensor_df,
            farm_lookup_df,
            sensor_type_lookup_df,
        )

        # Read currently active SCD2 versions from ClickHouse.
        current_dim_sensor_df = read_clickhouse(
            spark,
            """
            (
                SELECT *
                FROM dim_sensor FINAL
            ) AS dim_sensor
            """,
        ).filter(
            col("is_current") == 1,
        )

        # Add hashes to compare business attributes.
        #
        # The hash represents the state of the dimension row.
        # If the hash changes, a new SCD2 version is created.
        source_hashed_df = add_hash(
            source_sensor_df,
            [
                "farm_key",
                "sensor_type_key",
                "serial_number",
                "status",
                "installed_at",
            ],
        )

        current_hashed_df = add_hash(
            current_dim_sensor_df,
            [
                "farm_key",
                "sensor_type_key",
                "serial_number",
                "status",
                "installed_at",
            ],
        )

        # Detect new rows and changed rows.
        new_sensors_df, changed_sensors_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "sensor_id",
        )

        # Find currently active versions that need to expire.
        expired_sensors_df = current_dim_sensor_df.join(
            changed_sensors_df.select(
                "sensor_id",
            ),
            "sensor_id",
            "inner",
        )

        # Changed source rows become new active versions.
        new_sensors_version_df = changed_sensors_df

        # One version identifier for this warehouse load.
        load_version = int(
            time.time() * 1000,
        )

        rows_to_write = (
            build_new_version(
                new_sensors_df,
                load_version,
            )
            .unionByName(
                build_expired_version(
                    expired_sensors_df,
                    load_version,
                    "sensor_key",
                )
            )
            .unionByName(
                build_new_version(
                    new_sensors_version_df,
                    load_version,
                )
            )
        )

        if rows_to_write.count() > 0:
            write_clickhouse(
                rows_to_write,
                "dim_sensor",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
