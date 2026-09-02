"""Tests for the FastAPI application entry point."""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint_returns_status_message():
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
        patch("app.main.ensure_demo_users"),
    ):
        client = TestClient(app)
        response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Urban Green API is running"}


def test_lifespan_verifies_database_connection_on_startup():
    with (
        patch("app.main.verify_database_connection") as verify,
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
        patch("app.main.ensure_demo_users"),
        TestClient(app),
    ):
        pass

    verify.assert_called_once()


def test_lifespan_ensures_superuser_on_startup():
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser") as ensure,
        patch("app.main.ensure_demo_users"),
        TestClient(app),
    ):
        pass

    ensure.assert_called_once()


def test_lifespan_ensures_demo_users_on_startup():
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
        patch("app.main.ensure_demo_users") as ensure_demo,
        TestClient(app),
    ):
        pass

    ensure_demo.assert_called_once()


def test_metrics_endpoint_returns_prometheus_exposition():
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
        patch("app.main.ensure_demo_users"),
    ):
        client = TestClient(app)
        health_response = client.get("/health")
        response = client.get("/metrics")

    assert health_response.status_code == 200
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert 'handler="/health"' in response.text
    assert "/metrics" not in app.openapi()["paths"]
