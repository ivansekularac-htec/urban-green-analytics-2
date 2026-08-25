"""Deliver the rendered report HTML to the fake mailbox. Not a graph node."""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from airflow.sdk.bases.hook import BaseHook

from reports.state import OBJECT_KEY_TEMPLATE, SMTP_CONN_ID, STAGING_BUCKET

logger = logging.getLogger(__name__)


def send_report_email(html: str, report_date: str) -> None:
    """Send the same HTML that was published to MinIO."""
    conn = BaseHook.get_connection(SMTP_CONN_ID)
    msg = EmailMessage()
    msg["From"] = os.environ.get(
        "REPORT_EMAIL_FROM", "UrbanGreen Reports <reports@urbangreen.local>"
    )
    msg["To"] = os.environ.get("REPORT_EMAIL_TO", "exec@urbangreen.local")
    msg["Subject"] = f"UrbanGreen executive report {report_date}"
    msg.set_content(
        f"Daily executive report for {report_date}. "
        f"See also s3://{STAGING_BUCKET}/"
        f"{OBJECT_KEY_TEMPLATE.format(report_date=report_date)}"
    )
    msg.add_alternative(html, subtype="html")
    with smtplib.SMTP(conn.host, conn.port or 1025) as smtp:
        smtp.send_message(msg)
    logger.info(f"emailed report for {report_date}")
