import logging

from common.clickhouse import write_clickhouse_table
from common.config import WarehouseSettings
from common.minio import latest_rows, read_full_table
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_dim_user"
TARGET_TABLE = "dim_user"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        users_path = f"{settings.postgres_raw_root}/users/"

        # Read all source batches and keep the current row for each user.
        users = latest_rows(read_full_table(spark, users_path))

        # Transform the source data to match the ClickHouse schema.
        output = users.select(
            F.col("id").cast("long").alias("user_id"),
            F.trim(F.col("email")).alias("email"),
            F.trim(F.col("full_name")).alias("full_name"),
            F.col("is_active").cast("byte").alias("is_active"),
            F.from_unixtime(F.col("created_at")).cast("timestamp").alias("created_at"),
            F.current_timestamp().alias("_loaded_at"),
        )

        # Append the current SCD Type 1 snapshot to ClickHouse.
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
