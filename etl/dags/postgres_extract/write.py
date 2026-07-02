"""Object key layout and Parquet upload to the MinIO staging bucket."""

import io
import logging
import os

from airflow.providers.amazon.aws.hooks.s3 import S3Hook

logger = logging.getLogger(__name__)

MINIO_CONN_ID = "urbangreen_minio"
MINIO_STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")
STAGING_PREFIX = "raw/postgres"


def get_s3():
    """Return an S3 hook bound to the MinIO connection."""
    return S3Hook(aws_conn_id=MINIO_CONN_ID)


def flat_key(table, run_window):
    """Object key for a small, unpartitioned table under its run window folder."""
    return f"{STAGING_PREFIX}/{table}/{run_window}/{table}.parquet"


def partition_key(table, run_window, partition_label, day, chunk_index):
    """Object key for one day partition of a table inside its run window folder."""
    return (
        f"{STAGING_PREFIX}/{table}/{run_window}/{partition_label}={day}/"
        f"{table}__part{chunk_index:04d}.parquet"
    )


def write_parquet(s3, df, key):
    """Serialize a DataFrame to Parquet in memory and upload it as one object."""
    buf = io.BytesIO()
    df.to_parquet(buf, engine="pyarrow", index=False)
    s3.load_bytes(buf.getvalue(), key=key, bucket_name=MINIO_STAGING_BUCKET, replace=True)
    logger.info(f"wrote {len(df)} row(s) -> s3://{MINIO_STAGING_BUCKET}/{key}")
