"""
Executes the full refresh loading of the dim_crop dimension.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads all available crop and crop category data from raw parquet files
   stored in MinIO.
3. Selects the latest version of each dimension entity.
4. Transforms raw data into the dim_crop schema.
5. Writes the dimension dataframe into ClickHouse.

The loader is idempotent and can be executed multiple times
against the same raw data without changing the resulting dimension state.
"""

from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session
from dimensions.dim_crop import create_dim_crop


def main():
    """
    Runs the dim_crop ETL pipeline.

    The function creates a Spark session, generates the latest
    dimension state, writes it to ClickHouse, and stops the Spark job.

    Returns
    -------
    None
    """

    spark = get_spark_session("load-dim-crop")

    try:
        dim_crop_df = create_dim_crop(spark)

        if dim_crop_df.rdd.isEmpty():
            spark.stop()
            return

        write_to_clickhouse(
            dim_crop_df,
            "dim_crop",
            truncate=True,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
