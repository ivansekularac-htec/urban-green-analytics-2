from datetime import datetime

from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def upload_parquet(parquet_path, bucket, table):
    """
    Uploads a Parquet file to MinIO (S3-compatible storage) as part of the
    ingestion pipeline.

    The file is stored using a time-based object key to ensure:
    - historical traceability
    - no overwriting of previous ingestion results
    - support for replay/backfill scenarios

    Object key structure:
        {table}/ingestion_date={timestamp}/{table}.parquet

    Example:
        farms/ingestion_date=20260626T123000/farms.parquet

    Args:
        parquet_path (str):
            Local filesystem path to the Parquet file.

        bucket (str):
            Target MinIO bucket where data will be stored.

        table (str):
            Name of the source table (used for folder partitioning).

    Returns:
        str:
            The generated object key used to store the file in MinIO.

    Notes:
        - Uses Airflow S3Hook configured for MinIO compatibility
        - Each run produces an immutable file (append-only data lake pattern)
        - Enables downstream systems to build time-aware datasets
    """

    s3 = S3Hook(aws_conn_id="urbangreen_minio")

    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%S")

    object_key = f"{table}/ingestion_date={timestamp}/{table}.parquet"

    s3.load_file(
        filename=parquet_path,
        key=object_key,
        bucket_name=bucket,
        replace=True,
    )

    return object_key
