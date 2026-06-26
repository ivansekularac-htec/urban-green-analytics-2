"""
Storage layer for ingestion pipeline.

Responsible for:
- Uploading Parquet files to MinIO (S3-compatible storage)
- Using Airflow S3Hook with environment-configured connection ID
"""

from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from ingestion.config import MINIO_CONN_ID


def upload_parquet(parquet_path, bucket, object_key):
    """
    Uploads a Parquet file to object storage (MinIO/S3).

    Args:
        parquet_path (str): Local path of Parquet file
        bucket (str): Target bucket name (usually from env config)
        object_key (str): Full object path inside bucket

    Behavior:
        - Uses Airflow S3Hook
        - Overwrites existing object if replace=True
        - Requires valid AWS/MinIO connection in Airflow
    """

    # Initialize S3/MinIO connection via Airflow connection ID
    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)

    # Upload file to object storage
    s3.load_file(
        filename=parquet_path,
        key=object_key,
        bucket_name=bucket,
        replace=True,  # overwrite is intentional for idempotent ingestion
    )
