"""Tests for deterministic MinIO publishing and Mailpit delivery."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from reports import publishing
from reports.config import EmailSettings, MinioSettings

REPORT_DATE = date(2026, 8, 15)
HTML = "<!doctype html><html><body>Executive report</body></html>"

MINIO_SETTINGS = MinioSettings(
    endpoint="http://urbangreen-minio:9000",
    access_key="minioadmin",
    secret_key="secret",
    staging_bucket="staging",
)
EMAIL_SETTINGS = EmailSettings(
    host="urbangreen-mailpit",
    port=1025,
    sender="reports@urbangreen.local",
    recipients=("executives@urbangreen.local",),
    timeout_seconds=15,
)


def state():
    return {"report_date": REPORT_DATE, "html": HTML}


def run_publish():
    s3 = MagicMock()
    smtp = MagicMock()
    with (
        patch("reports.publishing.get_minio_settings", return_value=MINIO_SETTINGS),
        patch("reports.publishing.get_email_settings", return_value=EMAIL_SETTINGS),
        patch("reports.publishing.boto3.client", return_value=s3),
        patch("reports.publishing.smtplib.SMTP", return_value=smtp),
    ):
        output = publishing.publish_report(state())
    return output, s3, smtp.__enter__.return_value


def test_key_is_date_partitioned_and_stable():
    expected = "reports/executive/date=2026-08-15/report.html"

    assert publishing.object_key(REPORT_DATE) == expected
    assert publishing.object_key(date(2026, 8, 15)) == expected


def test_publish_overwrites_the_same_minio_object():
    output, s3, _ = run_publish()
    request = s3.put_object.call_args.kwargs

    assert request["Bucket"] == "staging"
    assert request["Key"] == "reports/executive/date=2026-08-15/report.html"
    assert request["Body"] == HTML.encode("utf-8")
    assert request["ContentType"] == "text/html; charset=utf-8"
    assert output["object_key"] == request["Key"]


def test_same_html_is_delivered_to_mailpit():
    output, _, smtp = run_publish()
    message = smtp.send_message.call_args.args[0]

    assert message["From"] == "reports@urbangreen.local"
    assert message["To"] == "executives@urbangreen.local"
    assert "2026-08-15" in message["Subject"]
    assert HTML in message.get_payload()[1].get_payload()
    assert output["email_sent"] is True


def test_storage_failure_is_visible_and_prevents_false_success():
    s3 = MagicMock()
    s3.put_object.side_effect = OSError("bucket unavailable")

    with (
        patch("reports.publishing.get_minio_settings", return_value=MINIO_SETTINGS),
        patch("reports.publishing.boto3.client", return_value=s3),
        patch("reports.publishing.smtplib.SMTP") as smtp,
        pytest.raises(OSError, match="bucket unavailable"),
    ):
        publishing.publish_report(state())

    smtp.assert_not_called()


def test_email_failure_is_visible_after_the_object_is_stored():
    smtp = MagicMock()
    smtp.return_value.__enter__.side_effect = OSError("smtp unavailable")

    with (
        patch("reports.publishing.get_minio_settings", return_value=MINIO_SETTINGS),
        patch("reports.publishing.get_email_settings", return_value=EMAIL_SETTINGS),
        patch("reports.publishing.boto3.client", return_value=MagicMock()),
        patch("reports.publishing.smtplib.SMTP", smtp),
        pytest.raises(OSError, match="smtp unavailable"),
    ):
        publishing.publish_report(state())
