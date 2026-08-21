"""Tests for publishing the report."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app import publish

DAY = date(2026, 8, 15)
HTML = "<html><body>report</body></html>"


def settings(**overrides) -> SimpleNamespace:
    values = {
        "minio_endpoint": "http://urbangreen-minio:9000",
        "minio_bucket": "staging",
        "minio_access_key": "minioadmin",
        "minio_secret_key": "secret",
        "smtp_host": "urbangreen-mailpit",
        "smtp_port": 1025,
        "email_from": "reports@urbangreen.local",
        "email_recipients": ["exec@urbangreen.local"],
    }
    values.update(overrides)

    return SimpleNamespace(**values)


def run(**overrides):
    """Publish with both sinks mocked; return the result and the two mocks."""

    s3 = MagicMock()
    smtp = MagicMock()

    with (
        patch("app.publish.get_settings", return_value=settings(**overrides)),
        patch("app.publish.boto3.client", return_value=s3),
        patch("app.publish.smtplib.SMTP", return_value=smtp),
    ):
        result = publish.publish(HTML, DAY)

    return result, s3, smtp.__enter__.return_value


def test_the_key_is_partitioned_by_date():
    assert publish.object_key(DAY) == "reports/executive/date=2026-08-15/report.html"


def test_the_same_day_always_writes_the_same_key():
    # Re-running a day replaces the object; it cannot add a second one.
    assert publish.object_key(DAY) == publish.object_key(date(2026, 8, 15))


def test_the_report_is_stored_as_html():
    result, s3, _ = run()

    s3.put_object.assert_called_once()
    call = s3.put_object.call_args.kwargs

    assert call["Bucket"] == "staging"
    assert call["Key"] == "reports/executive/date=2026-08-15/report.html"
    assert call["Body"] == HTML.encode("utf-8")
    assert call["ContentType"].startswith("text/html")
    assert result["stored"] is True


def test_the_report_is_emailed_to_the_recipients():
    result, _, smtp = run()

    message = smtp.send_message.call_args.args[0]

    assert message["To"] == "exec@urbangreen.local"
    assert message["From"] == "reports@urbangreen.local"
    assert "2026-08-15" in message["Subject"]
    assert HTML in message.get_payload()[1].get_payload()
    assert result["emailed"] is True


def test_a_storage_failure_still_leaves_the_email_sent():
    s3 = MagicMock()
    s3.put_object.side_effect = OSError("bucket is gone")

    with (
        patch("app.publish.get_settings", return_value=settings()),
        patch("app.publish.boto3.client", return_value=s3),
        patch("app.publish.smtplib.SMTP", return_value=MagicMock()),
    ):
        result = publish.publish(HTML, DAY)

    assert result["stored"] is False
    assert result["emailed"] is True
    assert "storage" in result["warnings"][0]


def test_a_mail_failure_still_leaves_the_object_stored():
    with (
        patch("app.publish.get_settings", return_value=settings()),
        patch("app.publish.boto3.client", return_value=MagicMock()),
        patch("app.publish.smtplib.SMTP", side_effect=OSError("connection refused")),
    ):
        result = publish.publish(HTML, DAY)

    assert result["stored"] is True
    assert result["emailed"] is False
    assert "email" in result["warnings"][0]


def test_publishing_without_recipients_is_a_warning_not_a_crash():
    result, _, _ = run(email_recipients=[])

    assert result["stored"] is True
    assert result["emailed"] is False
    assert result["warnings"]
