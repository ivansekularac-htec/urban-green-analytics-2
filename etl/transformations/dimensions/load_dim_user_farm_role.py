"""Rebuild user, farm, and role assignment history in an SCD2 dimension."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from transformations.common.clickhouse import read_clickhouse_table
from transformations.common.config import load_settings
from transformations.common.lake_reader import read_postgres_table
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

TARGET_TABLE = "dim_user_farm_role"
OPEN_END = "2099-12-31 23:59:59"


def transform(
    user_roles: DataFrame,
    users: DataFrame,
    roles: DataFrame,
    farms: DataFrame,
) -> DataFrame:
    user_roles = (
        user_roles.withColumn(
            "_version",
            F.coalesce("updated_at", "created_at").cast("long"),
        )
        .withColumn(
            "valid_from",
            F.to_timestamp(F.from_unixtime("_version")),
        )
        .dropDuplicates(["id", "valid_from"])
        .alias("ur")
    )

    users = users.select(
        "user_id",
        "full_name",
    ).alias("u")

    roles = roles.select(
        "role_id",
        F.col("name").alias("role_name"),
    ).alias("r")

    farms = farms.select(
        "farm_id",
        "farm_key",
        F.col("name").alias("farm_name"),
        "valid_from",
        "valid_to",
    ).alias("f")

    result = (
        user_roles.join(
            users,
            F.col("ur.user_id") == F.col("u.user_id"),
            "left",
        )
        .join(
            roles,
            F.col("ur.role_id") == F.col("r.role_id"),
            "left",
        )
        .join(
            farms,
            (F.col("ur.farm_id") == F.col("f.farm_id"))
            & (F.col("ur.valid_from") >= F.col("f.valid_from"))
            & (F.col("ur.valid_from") < F.col("f.valid_to")),
            "left",
        )
    )

    window = Window.partitionBy(F.col("ur.id")).orderBy(F.col("ur.valid_from"))

    return result.withColumn(
        "_next_valid_from",
        F.lead(F.col("ur.valid_from")).over(window),
    ).select(
        F.col("ur.id").cast("long").alias("user_role_id"),
        F.col("ur.user_id").cast("long").alias("user_id"),
        F.col("ur.role_id").cast("long").alias("role_id"),
        F.coalesce("f.farm_key", F.lit(0)).cast("long").alias("farm_key"),
        F.coalesce("ur.farm_id", F.lit(0)).cast("long").alias("farm_id"),
        F.col("u.full_name").alias("user_full_name"),
        F.col("r.role_name"),
        F.coalesce("f.farm_name", F.lit("")).alias("farm_name"),
        F.col("ur.valid_from"),
        F.coalesce(
            "_next_valid_from",
            F.lit(OPEN_END).cast("timestamp"),
        ).alias("valid_to"),
        F.col("_next_valid_from").isNull().cast("byte").alias("is_current"),
        F.col("ur._version"),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(TARGET_TABLE, settings)

    try:
        result = transform(
            read_postgres_table(
                spark,
                settings,
                "user_roles",
            ),
            read_clickhouse_table(
                spark,
                settings,
                "dim_user",
            ),
            read_clickhouse_table(
                spark,
                settings,
                "dim_role",
            ),
            read_clickhouse_table(
                spark,
                settings,
                "dim_farm",
            ),
        )

        full_refresh_table(
            result,
            settings,
            TARGET_TABLE,
        )

        logging.info("Loaded %s", TARGET_TABLE)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
