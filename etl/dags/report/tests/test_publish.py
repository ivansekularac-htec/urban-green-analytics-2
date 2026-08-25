"""Tests for executive report publishing."""

import os
from unittest import TestCase
from unittest.mock import MagicMock, call, patch

from report.publish import (
    _publish_to_minio,
    _send_email,
    publish_report,
)


class PublishReportTests(TestCase):
    def test_minio_uses_airflow_connection_in_task(self):
        connection = MagicMock()
        connection.login = "minio-user"
        connection.password = "minio-password"
        connection.extra_dejson = {
            "endpoint_url": "http://urbangreen-minio:9000",
        }

        connections = MagicMock()
        connections.get.return_value = connection

        s3_client = MagicMock()

        with (
            patch(
                "report.publish.get_current_context",
                return_value={"conn": connections},
            ),
            patch("report.publish.boto3.client", return_value=s3_client) as boto_client,
        ):
            _publish_to_minio(
                "staging",
                "reports/executive/date=2026-08-20/report.html",
                "<html>report</html>",
            )

        connections.get.assert_called_once_with("urbangreen_minio")

        boto_client.assert_called_once_with(
            "s3",
            endpoint_url="http://urbangreen-minio:9000",
            aws_access_key_id="minio-user",
            aws_secret_access_key="minio-password",
        )

        s3_client.put_object.assert_called_once_with(
            Bucket="staging",
            Key="reports/executive/date=2026-08-20/report.html",
            Body=b"<html>report</html>",
            ContentType="text/html; charset=utf-8",
        )

    def test_minio_uses_environment_standalone(self):
        s3_client = MagicMock()

        with (
            patch("report.publish.get_current_context", side_effect=RuntimeError),
            patch.dict(
                os.environ,
                {
                    "MINIO_ENDPOINT": "http://urbangreen-minio:9000",
                    "MINIO_ROOT_USER": "minio-user",
                    "MINIO_ROOT_PASSWORD": "minio-password",
                },
            ),
            patch("report.publish.boto3.client", return_value=s3_client) as boto_client,
        ):
            _publish_to_minio(
                "staging",
                "reports/executive/date=2026-08-20/report.html",
                "<html>report</html>",
            )

        boto_client.assert_called_once_with(
            "s3",
            endpoint_url="http://urbangreen-minio:9000",
            aws_access_key_id="minio-user",
            aws_secret_access_key="minio-password",
        )

        s3_client.put_object.assert_called_once_with(
            Bucket="staging",
            Key="reports/executive/date=2026-08-20/report.html",
            Body=b"<html>report</html>",
            ContentType="text/html; charset=utf-8",
        )

    def test_publish_report_returns_expected_key(self):
        expected_key = "reports/executive/date=2026-08-20/report.html"

        state = {"report_date": "2026-08-20", "html": "<html>report</html>"}

        with (
            patch("report.publish.minio_staging_bucket", return_value="staging"),
            patch("report.publish._publish_to_minio") as publish_to_minio,
            patch("report.publish._send_email") as send_email,
        ):
            result = publish_report(state)

        self.assertEqual(
            result,
            {"object_key": expected_key},
        )

        publish_to_minio.assert_called_once_with(
            "staging",
            expected_key,
            "<html>report</html>",
        )

        send_email.assert_called_once_with("2026-08-20", "<html>report</html>")

    def test_publish_report_uses_same_key_on_rerun(self):
        expected_key = "reports/executive/date=2026-08-20/report.html"

        state = {
            "report_date": "2026-08-20",
            "html": "<html>report</html>",
        }

        with (
            patch("report.publish.minio_staging_bucket", return_value="staging"),
            patch("report.publish._publish_to_minio") as publish_to_minio,
            patch("report.publish._send_email"),
        ):
            first = publish_report(state)
            second = publish_report(state)

        self.assertEqual(first["object_key"], expected_key)
        self.assertEqual(second["object_key"], expected_key)

        self.assertEqual(
            publish_to_minio.call_args_list,
            [
                call("staging", expected_key, "<html>report</html>"),
                call("staging", expected_key, "<html>report</html>"),
            ],
        )

    def test_send_email_uses_mailpit_smtp(self):
        smtp = MagicMock()
        smtp_context = smtp.return_value.__enter__.return_value

        with (
            patch(
                "report.publish.report_email_to",
                return_value=("alice@urbangreen.local,bob@urbangreen.local"),
            ),
            patch(
                "report.publish.report_email_from",
                return_value="reports@urbangreen.local",
            ),
            patch("report.publish.report_smtp_host", return_value="urbangreen-mailpit"),
            patch("report.publish.report_smtp_port", return_value=1025),
            patch("report.publish.smtplib.SMTP", smtp),
        ):
            _send_email("2026-08-20", "<html><body>Daily report</body></html>")

        smtp.assert_called_once_with(
            "urbangreen-mailpit",
            1025,
            timeout=15,
        )

        smtp_context.send_message.assert_called_once()

        message = smtp_context.send_message.call_args.args[0]

        self.assertEqual(message["Subject"], "UrbanGreen Executive Report - 2026-08-20")
        self.assertEqual(message["From"], "reports@urbangreen.local")
        self.assertEqual(
            message["To"],
            ("alice@urbangreen.local, bob@urbangreen.local"),
        )

        html_body = message.get_body(preferencelist=("html",))

        self.assertIsNotNone(html_body)
        self.assertIn("Daily report", html_body.get_content())

    def test_send_email_rejects_empty_recipient_list(self):
        with patch("report.publish.report_email_to", return_value=" , "):
            with self.assertRaisesRegex(
                ValueError, "REPORT_EMAIL_TO must contain at least one address"
            ):
                _send_email("2026-08-20", "<html>report</html>")
