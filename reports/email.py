"""Send UrbanGreen executive reports by email."""

import logging
import smtplib
from email.message import EmailMessage

from reports.config import get_email_settings
from reports.models import ReportState

logger = logging.getLogger(__name__)


def send_report_email(state: ReportState) -> dict[str, bool]:
    """Send the rendered executive report by email."""
    settings = get_email_settings()

    message = EmailMessage()
    message["Subject"] = f"UrbanGreen Executive Report - {state['report_date']}"
    message["From"] = settings.sender
    message["To"] = ", ".join(settings.recipients)

    message.set_content(
        f"UrbanGreen Executive Report for {state['report_date']}. "
        "Please use an HTML-capable email client to view the report."
    )
    message.add_alternative(state["html"], subtype="html")

    with smtplib.SMTP(settings.host, settings.port, timeout=15) as smtp:
        if settings.use_tls:
            smtp.starttls()

        if settings.user and settings.password:
            smtp.login(settings.user, settings.password)

        smtp.send_message(message)

    logger.info(
        f"Sent executive report for {state['report_date']} to "
        f"{', '.join(settings.recipients)}"
    )

    return {"email_sent": True}
