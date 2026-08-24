"""Fifth node: send the same document to the mail sink.

Email is the second sink, not the deliverable, so its failure is a warning
rather than a raised error: the object is already stored by the time this runs,
and a bounced mail is a partial success, not a total one. The HTML body is the
same document that was stored - one render, two destinations.
"""

from __future__ import annotations

import logging
import smtplib
from collections.abc import Callable
from email.message import EmailMessage

from report.deps import ReportDeps
from report.state import ReportState

logger = logging.getLogger(__name__)

_SMTP_TIMEOUT_SECONDS = 10


def build_message(
    sender: str, recipient: str, report_date: str, html: str
) -> EmailMessage:
    """Assemble the report email. Pure, so the headers and body are testable."""
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = f"UrbanGreen Executive Report — {report_date}"
    message.set_content(
        "This report is best viewed as HTML. "
        f"The executive report for {report_date} is attached as the HTML body."
    )
    message.add_alternative(html, subtype="html")
    return message


def make_email(deps: ReportDeps) -> Callable[[ReportState], dict]:
    """Build the email node against an SMTP sink."""

    def email(state: ReportState) -> dict:
        message = build_message(
            deps.email.sender,
            deps.email.recipient,
            state["report_date"],
            state["html"],
        )

        try:
            with smtplib.SMTP(
                deps.email.host, deps.email.port, timeout=_SMTP_TIMEOUT_SECONDS
            ) as smtp:
                smtp.send_message(message)
        except (OSError, smtplib.SMTPException) as exc:
            # The object is already stored; a failed send is a partial success.
            logger.warning(f"report email not sent: {exc}")
            return {"email_sent": False}

        logger.info(f"report email sent to {deps.email.recipient}")
        return {"email_sent": True}

    return email
