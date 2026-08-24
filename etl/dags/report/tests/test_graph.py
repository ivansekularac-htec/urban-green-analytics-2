"""End-to-end test of the compiled graph against fakes.

Drives the whole pipeline with a fake warehouse, a stubbed model, a fake S3 and
a stubbed SMTP, so the order of stages and the final state are exercised without
any real I/O.
"""

from unittest.mock import patch

from report.deps import EmailConfig, OllamaConfig, ReportDeps
from report.graph import run_report
from report.nodes import summarize
from report.nodes.summarize import SOURCE_FALLBACK, SOURCE_MODEL
from report.tests.conftest import FakeResult, FakeS3, FakeWarehouse


def _warehouse():
    return FakeWarehouse(
        [
            FakeResult(
                [
                    "total_yield_kg",
                    "total_energy_kwh",
                    "energy_efficiency_kwh_per_kg",
                    "non_premium_share",
                    "compliance_rate",
                    "anomaly_rate",
                    "farms_reporting",
                ],
                [(1234.5, 8900.0, 7.21, 0.34, 0.97, 0.03, 70)],
            ),
            FakeResult(["active_farms"], [(75,)]),
            FakeResult(
                [
                    "rank",
                    "farm",
                    "city",
                    "total_yield_kg",
                    "premium_yield_share",
                    "energy_efficiency_kwh_per_kg",
                ],
                [(1, "UG Farm 043", "Berlin", 31.824, 0.585, 5.1)],
            ),
            FakeResult(
                ["sensor_type", "unit", "readings", "anomalies"],
                [("pH Level", "pH", 300, 1)],
            ),
        ]
    )


def _deps(warehouse=None, s3=None):
    return ReportDeps(
        warehouse=warehouse or _warehouse(),
        s3=s3 or FakeS3(),
        bucket="staging",
        ollama=OllamaConfig(
            host="ollama:11434", model="m", num_predict=200, timeout_seconds=30
        ),
        email=EmailConfig(host="mailpit", port=1025, sender="f@x", recipient="t@x"),
    )


def test_a_full_run_stores_and_emails_with_a_model_summary():
    s3 = FakeS3()
    deps = _deps(s3=s3)

    with (
        patch.object(
            summarize, "call_ollama", return_value="Good day.\n- up\n- steady"
        ),
        patch("report.nodes.email.smtplib.SMTP"),
    ):
        state = run_report(deps, "2026-08-15")

    assert state["object_key"] == "reports/executive/date=2026-08-15/report.html"
    assert state["summary_source"] == SOURCE_MODEL
    assert state["email_sent"] is True
    # The stored body is the rendered report.
    assert s3.puts[0]["Body"].startswith(b"<!DOCTYPE html>")
    assert b"UG Farm 043" in s3.puts[0]["Body"]


def test_a_run_with_a_cold_model_still_stores_but_marks_fallback():
    s3 = FakeS3()
    deps = _deps(s3=s3)

    with (
        patch.object(summarize, "call_ollama", side_effect=TimeoutError("cold")),
        patch("report.nodes.email.smtplib.SMTP"),
    ):
        state = run_report(deps, "2026-08-15")

    # The pipeline still produces the object, but the fallback is visible so the
    # DAG can decide to fail on it.
    assert state["object_key"]
    assert state["summary_source"] == SOURCE_FALLBACK
    assert len(s3.puts) == 1
