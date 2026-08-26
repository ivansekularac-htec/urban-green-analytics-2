"""Publish reports to MinIO and deliver them to the local email inbox."""

import logging
import smtplib
from datetime import date
from email.message import EmailMessage

import boto3

from reports.config import get_email_settings, get_minio_settings
from reports.models import ReportState

logger = logging.getLogger(__name__)

REPORT_OBJECT_PREFIX = "reports/executive"


def object_key(report_date: date) -> str:
    """Return the deterministic object key for a report date."""

    return f"{REPORT_OBJECT_PREFIX}/date={report_date.isoformat()}/report.html"


def _store_html(html: str, report_date: date) -> tuple[str, str]:
    """Upload HTML to MinIO, replacing the same date's previous object."""

    settings = get_minio_settings()
    key = object_key(report_date)
    client = boto3.client(
        "s3",
        endpoint_url=settings.endpoint,
        aws_access_key_id=settings.access_key,
        aws_secret_access_key=settings.secret_key,
        region_name="us-east-1",
    )
    client.put_object(
        Bucket=settings.staging_bucket,
        Key=key,
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )
    return settings.staging_bucket, key


def _send_email(html: str, report_date: date) -> None:
    """Send the same rendered HTML to the configured Mailpit inbox."""

    settings = get_email_settings()
    message = EmailMessage()
    message["Subject"] = f"UrbanGreen Executive Report - {report_date.isoformat()}"
    message["From"] = settings.sender
    message["To"] = ", ".join(settings.recipients)
    message.set_content(
        f"UrbanGreen executive report for {report_date.isoformat()}. "
        "Open this message in an HTML-capable email client."
    )
    message.add_alternative(html, subtype="html")

    with smtplib.SMTP(
        settings.host,
        settings.port,
        timeout=settings.timeout_seconds,
    ) as smtp:
        smtp.send_message(message)


def publish_report(state: ReportState) -> dict[str, object]:
    """Store and email the report, failing visibly if either delivery fails."""

    report_date = state["report_date"]
    bucket, key = _store_html(state["html"], report_date)
    logger.info("Published executive report to s3://%s/%s", bucket, key)

    _send_email(state["html"], report_date)
    logger.info("Sent executive report email for %s", report_date)

    return {
        "published_bucket": bucket,
        "object_key": key,
        "email_sent": True,
    }
