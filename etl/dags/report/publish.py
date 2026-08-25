"""Publishing for the daily executive report."""

import logging
import smtplib
from email.message import EmailMessage

import boto3
from airflow.sdk import get_current_context

from report.config import (
    minio_access_key,
    minio_endpoint,
    minio_secret_key,
    minio_staging_bucket,
    report_email_from,
    report_email_to,
    report_smtp_host,
    report_smtp_port,
)
from report.state import ReportState

logger = logging.getLogger(__name__)

MINIO_CONN_ID = "urbangreen_minio"
REPORT_PREFIX = "reports/executive"
SMTP_TIMEOUT_SECONDS = 15


def _get_minio_client():
    """Create a MinIO client for Airflow or standalone execution."""
    try:
        context = get_current_context()
    except RuntimeError:
        context = None

    if context:
        connection = context["conn"].get(MINIO_CONN_ID)

        return boto3.client(
            "s3",
            endpoint_url=connection.extra_dejson["endpoint_url"],
            aws_access_key_id=connection.login,
            aws_secret_access_key=connection.password,
        )

    return boto3.client(
        "s3",
        endpoint_url=minio_endpoint(),
        aws_access_key_id=minio_access_key(),
        aws_secret_access_key=minio_secret_key(),
    )


def _send_email(
    report_date: str,
    html: str,
) -> None:
    """Send the rendered report through Mailpit."""
    email_to = report_email_to()

    recipients = [address.strip() for address in email_to.split(",") if address.strip()]

    if not recipients:
        raise ValueError("REPORT_EMAIL_TO must contain at least one address.")

    message = EmailMessage()

    message["Subject"] = f"UrbanGreen Executive Report - {report_date}"
    message["From"] = report_email_from()
    message["To"] = ", ".join(recipients)

    message.set_content(f"UrbanGreen executive report for {report_date}.")

    message.add_alternative(html, subtype="html")

    with smtplib.SMTP(
        report_smtp_host(),
        report_smtp_port(),
        timeout=SMTP_TIMEOUT_SECONDS,
    ) as smtp:
        smtp.send_message(message)

    logger.info(f"Sent executive report email to {', '.join(recipients)}.")


def _publish_to_minio(
    bucket: str,
    object_key: str,
    html: str,
) -> None:
    """Write the report to MinIO."""
    client = _get_minio_client()

    client.put_object(
        Bucket=bucket,
        Key=object_key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )


def publish_report(
    state: ReportState,
) -> dict[str, str]:
    """Publish the report to MinIO and send it by email."""
    report_date = state["report_date"]
    bucket = minio_staging_bucket()

    object_key = f"{REPORT_PREFIX}/date={report_date}/report.html"

    _publish_to_minio(bucket, object_key, state["html"])

    logger.info(f"Published executive report -> s3://{bucket}/{object_key}")

    _send_email(report_date, state["html"])

    return {"object_key": object_key}
