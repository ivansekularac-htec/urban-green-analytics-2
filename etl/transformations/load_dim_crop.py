import os

from transformations.common import create_spark, read_parquet

MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")


def main():
    spark = create_spark("load_dim_crop")

    df = read_parquet(
        spark,
        f"s3a://{MINIO_STAGING_BUCKET}/raw/postgres/crops/",
    )

    # View your schema and rows
    df.printSchema()
    df.show()

    # transformations

    spark.stop()


if __name__ == "__main__":
    main()
