import logging

from common.clickhouse import write_clickhouse_table
from common.config import WarehouseSettings
from common.minio import latest_rows, read_full_table
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_dim_crop"
TARGET_TABLE = "dim_crop"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        crops_path = f"{settings.postgres_raw_root}/crops/"
        categories_path = f"{settings.postgres_raw_root}/crop_categories/"

        # Read all crop batches and keep the latest row for each crop.
        crops = latest_rows(
            read_full_table(
                spark,
                crops_path,
            )
        ).select(
            F.col("id").cast("long").alias("crop_id"),
            F.trim(F.col("name")).alias("name"),
            F.coalesce(F.trim(F.col("description")), F.lit("")).alias("description"),
            F.col("category_id").cast("long").alias("crop_category_id"),
        )

        # Read all category batches and keep the latest row
        # for each crop category.
        categories = latest_rows(
            read_full_table(
                spark,
                categories_path,
            )
        ).select(
            F.col("id").cast("long").alias("crop_category_id"),
            F.trim(F.col("name")).alias("category_name"),
        )

        # Join crops with the current crop category values.
        output = (
            crops.join(
                F.broadcast(categories),
                on="crop_category_id",
                how="inner",
            )
            .withColumn("_loaded_at", F.current_timestamp())
            .select(
                "crop_id",
                "name",
                "description",
                "crop_category_id",
                "category_name",
                "_loaded_at",
            )
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
