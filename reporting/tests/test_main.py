"""Tests for the reporting application entry point."""

from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import create_app, main


def test_health_reports_the_service_is_alive():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_main_serves_the_built_app_with_configured_settings():
    settings = SimpleNamespace(
        host="127.0.0.1",
        port=9002,
        log_level="INFO",
    )

    with (
        patch("app.main.get_settings", return_value=settings),
        patch("app.main.uvicorn.run") as run,
    ):
        main()

    run.assert_called_once()
    _, kwargs = run.call_args

    assert kwargs["host"] == "127.0.0.1"
    assert kwargs["port"] == 9002
    assert kwargs["log_level"] == "info"
