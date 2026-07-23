"""
Executes the full refresh loading of the dim_quality_grade dimension.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads all available quality grade data from raw parquet files
   stored in MinIO.
3. Selects the latest record for each quality grade.
4. Transforms raw data into the dim_quality_grade schema.
5. Writes the dimension dataframe into ClickHouse.

The loader is idempotent and can be executed multiple times
against the same raw data without changing the resulting dimension state.
"""

from common.clickhouse import write_to_clickhouse
from common.spark import get_spark_session
from dimensions.dim_quality_grade import create_dim_quality_grade


def main():
    """
    Runs the dim_quality_grade ETL pipeline.

    The function creates a Spark session, generates the latest
    dimension state, writes it into ClickHouse, and stops the Spark job.

    Returns
    -------
    None
    """

    spark = get_spark_session("load-dim-quality-grade")

    try:
        dim_quality_grade_df = create_dim_quality_grade(spark)

        if dim_quality_grade_df.rdd.isEmpty():
            spark.stop()
            return

        write_to_clickhouse(
            dim_quality_grade_df,
            "dim_quality_grade",
            truncate=True,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
