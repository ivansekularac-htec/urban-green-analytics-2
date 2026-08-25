"""Write the rendered report to the staging bucket, overwriting the same date key."""

from __future__ import annotations

import logging

from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from reports.state import MINIO_CONN_ID, OBJECT_KEY_TEMPLATE, STAGING_BUCKET, ReportState

logger = logging.getLogger(__name__)


def publish(state: ReportState) -> dict:
    """Overwrite the date-partitioned HTML object in the staging bucket."""
    key = OBJECT_KEY_TEMPLATE.format(report_date=state["report_date"])
    s3 = S3Hook(aws_conn_id=MINIO_CONN_ID)
    s3.load_bytes(
        state["html"].encode("utf-8"),
        key=key,
        bucket_name=STAGING_BUCKET,
        replace=True,
    )
    logger.info(f"published s3://{STAGING_BUCKET}/{key}")
    return {"object_key": key}
