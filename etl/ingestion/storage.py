from airflow.providers.amazon.aws.hooks.s3 import S3Hook


def upload_parquet(parquet_path, bucket, object_key):
    """
    Uploads a Parquet file to MinIO using the provided object key.
    """

    s3 = S3Hook(aws_conn_id="urbangreen_minio")

    s3.load_file(
        filename=parquet_path,
        key=object_key,
        bucket_name=bucket,
        replace=True,
    )
