"""Tests for the reporting application entry point."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app, main, resolve_day

DAY = date(2026, 8, 15)

STATE = {
    "summary": {"source": "qwen3.5:2b"},
    "published": {
        "key": "reports/executive/date=2026-08-15/report.html",
        "stored": True,
        "emailed": True,
        "warnings": [],
    },
}


def test_health_reports_the_service_is_alive():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_a_report_request_returns_the_published_key():
    client = TestClient(create_app())

    with patch("app.main.graph.run", return_value=STATE) as run:
        response = client.post("/reports/2026-08-15")

    run.assert_called_once_with(DAY)
    assert response.status_code == 200
    assert response.json() == {
        "day": "2026-08-15",
        "key": "reports/executive/date=2026-08-15/report.html",
        "stored": True,
        "emailed": True,
        "summary_source": "qwen3.5:2b",
        "warnings": [],
    }


def test_an_unreadable_day_is_rejected():
    client = TestClient(create_app())

    response = client.post("/reports/not-a-date")

    assert response.status_code == 400


def test_latest_resolves_to_the_newest_loaded_day():
    with (
        patch("app.main.metrics.get_client"),
        patch("app.main.metrics.latest_date", return_value=DAY),
    ):
        assert resolve_day("latest") == DAY


def test_latest_fails_when_the_warehouse_is_empty():
    client = TestClient(create_app())

    with (
        patch("app.main.metrics.get_client"),
        patch("app.main.metrics.latest_date", return_value=None),
    ):
        response = client.post("/reports/latest")

    assert response.status_code == 400


def test_the_cli_runs_one_day_and_exits():
    with (
        patch("sys.argv", ["main", "--date", "2026-08-15"]),
        patch("app.main.get_settings", return_value=SimpleNamespace(log_level="INFO")),
        patch("app.main.graph.run", return_value=STATE),
        patch("app.main.uvicorn.run") as serve,
    ):
        main()

    serve.assert_not_called()


def test_serving_uses_the_configured_host_and_port():
    settings = SimpleNamespace(host="127.0.0.1", port=9002, log_level="INFO")

    with (
        patch("sys.argv", ["main"]),
        patch("app.main.get_settings", return_value=settings),
        patch("app.main.uvicorn.run") as serve,
    ):
        main()

    assert serve.call_args.kwargs["host"] == "127.0.0.1"
    assert serve.call_args.kwargs["port"] == 9002
