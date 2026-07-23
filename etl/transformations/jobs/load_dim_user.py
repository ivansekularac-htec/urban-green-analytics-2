"""
Executes the full refresh loading of the dim_user dimension.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads all available user data from raw parquet files
   stored in MinIO.
3. Selects the latest record for each user.
4. Transforms raw data into the dim_user schema.
5. Writes the dimension dataframe into ClickHouse.

The loader is idempotent and can be executed multiple times
against the same raw data without changing the resulting dimension state.
"""

from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session
from dimensions.dim_user import create_dim_user


def main():
    """
    Runs the dim_user ETL pipeline.

    The function creates a Spark session, generates the latest
    dimension state, writes it into ClickHouse, and stops the Spark job.

    Returns
    -------
    None
    """

    spark = get_spark_session("load-dim-user")

    try:
        dim_user_df = create_dim_user(spark)

        if dim_user_df.rdd.isEmpty():
            spark.stop()
            return

        write_to_clickhouse(
            dim_user_df,
            "dim_user",
            truncate=True,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
