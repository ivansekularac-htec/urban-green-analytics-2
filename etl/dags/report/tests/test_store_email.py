"""Tests for the two publishing nodes.

Store must fail loudly and be idempotent by key; email must warn rather than
fail, since the object is the deliverable and the mail is the second sink.
"""

import smtplib
from unittest.mock import patch

import pytest

from report.nodes.email import build_message, make_email
from report.nodes.store import make_store, object_key
from report.tests.conftest import FakeS3


def test_the_key_is_date_partitioned_and_deterministic():
    assert object_key("2026-08-15") == "reports/executive/date=2026-08-15/report.html"
    assert object_key("2026-08-15") == object_key("2026-08-15")


def test_store_writes_the_html_at_the_key(deps):
    node = make_store(deps)

    result = node({"report_date": "2026-08-15", "html": "<html>x</html>"})

    put = deps.s3.puts[0]
    assert result["object_key"] == "reports/executive/date=2026-08-15/report.html"
    assert put["Bucket"] == "staging"
    assert put["Key"] == "reports/executive/date=2026-08-15/report.html"
    assert put["Body"] == b"<html>x</html>"
    assert put["ContentType"].startswith("text/html")


def test_rerunning_a_date_writes_the_same_key(deps):
    node = make_store(deps)

    node({"report_date": "2026-08-15", "html": "<html>1</html>"})
    node({"report_date": "2026-08-15", "html": "<html>2</html>"})

    keys = {put["Key"] for put in deps.s3.puts}
    assert keys == {"reports/executive/date=2026-08-15/report.html"}


def test_store_raises_when_the_write_fails(deps):
    """The object is the deliverable, so a failed write must fail the run."""

    class Boom(FakeS3):
        def put_object(self, **kwargs):
            raise RuntimeError("bucket unreachable")

    deps.s3 = Boom()
    node = make_store(deps)

    with pytest.raises(RuntimeError):
        node({"report_date": "2026-08-15", "html": "<html>x</html>"})


def test_email_message_has_an_html_body():
    message = build_message("from@x", "to@x", "2026-08-15", "<html>report</html>")

    assert message["Subject"].endswith("2026-08-15")
    html_part = message.get_body(preferencelist=("html",))
    assert "<html>report</html>" in html_part.get_content()


def test_email_sent_flag_is_true_on_success(deps):
    node = make_email(deps)

    with patch("report.nodes.email.smtplib.SMTP") as smtp:
        result = node({"report_date": "2026-08-15", "html": "<html>x</html>"})

    assert result["email_sent"] is True
    smtp.assert_called_once()


def test_email_failure_is_a_warning_not_a_raise(deps):
    """The object is already stored; a bounced mail is a partial success."""
    node = make_email(deps)

    with patch(
        "report.nodes.email.smtplib.SMTP", side_effect=smtplib.SMTPException("no sink")
    ):
        result = node({"report_date": "2026-08-15", "html": "<html>x</html>"})

    assert result["email_sent"] is False
