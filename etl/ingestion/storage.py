"""
Storage layer for ingestion pipeline.

Responsible for:
- Uploading Parquet data to MinIO (S3-compatible storage)
- Using Airflow S3Hook with environment-configured connection ID
"""

from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from ingestion.config import MINIO_CONN_ID


def upload_parquet(parquet_bytes, bucket, object_key):
    """
    Uploads Parquet data to object storage (MinIO/S3).

    Args:
        parquet_bytes (bytes):
            Serialized Parquet file contents.

        bucket (str):
            Target bucket name.

        object_key (str):
            Destination object path inside the bucket.

    Behavior:
        - Uses Airflow S3Hook
        - Uploads directly from memory
        - Overwrites existing objects for idempotent ingestion
    """

    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)

    s3.load_bytes(
        bytes_data=parquet_bytes,
        key=object_key,
        bucket_name=bucket,
        replace=True,
    )
