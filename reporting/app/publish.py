"""Publishes the finished report: an object in the bucket and an email.

Each sink is tried on its own. One of them failing is recorded as a warning
rather than raised, so a run still delivers the report the other way.
"""

import logging
import smtplib
from datetime import date
from email.message import EmailMessage

import boto3

from app.config import get_settings

logger = logging.getLogger(__name__)

S3_PREFIX = "reports/executive"
SMTP_TIMEOUT_SECONDS = 10


def object_key(day: date) -> str:
    """Return the bucket key for a day's report."""

    return f"{S3_PREFIX}/date={day}/report.html"


def publish(html: str, day: date) -> dict:
    """Store the report in the bucket and email it to the recipients."""

    result = {"key": object_key(day), "stored": False, "emailed": False, "warnings": []}

    try:
        _store(html, day)
        result["stored"] = True
    except Exception as exc:
        logger.warning("could not store the report (%s)", exc)
        result["warnings"].append(f"storage: {exc}")

    try:
        _email(html, day)
        result["emailed"] = True
    except Exception as exc:
        logger.warning("could not email the report (%s)", exc)
        result["warnings"].append(f"email: {exc}")

    return result


def _store(html: str, day: date) -> None:
    """Upload the report, replacing any earlier run for the same day."""

    settings = get_settings()

    client = boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
        region_name="us-east-1",
    )

    # Same day, same key: a re-run replaces the object instead of adding one.
    client.put_object(
        Bucket=settings.minio_bucket,
        Key=object_key(day),
        Body=html.encode("utf-8"),
        ContentType="text/html; charset=utf-8",
    )


def _email(html: str, day: date) -> None:
    """Send the report as an HTML email."""

    settings = get_settings()
    recipients = settings.email_recipients

    if not recipients:
        raise ValueError("no recipients are configured")

    message = EmailMessage()
    message["Subject"] = f"UrbanGreen Executive Report - {day}"
    message["From"] = settings.email_from
    message["To"] = ", ".join(recipients)
    message.set_content("This report is best viewed in an HTML mail client.")
    message.add_alternative(html, subtype="html")

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=SMTP_TIMEOUT_SECONDS) as smtp:
        smtp.send_message(message)
