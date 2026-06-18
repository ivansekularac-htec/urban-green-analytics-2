"""Tests for the FastAPI application entry point."""

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint_returns_status_message():
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Urban Green API is running"}


def test_lifespan_verifies_database_connection_on_startup():
    with (
        patch("app.main.verify_database_connection") as verify,
        TestClient(app),
    ):
        pass

    verify.assert_called_once()


def test_lifespan_verifies_database_connection_on_startup(monkeypatch):
    verify_mock = MagicMock()
    ensure_superuser_mock = MagicMock()
    session_mock = MagicMock()

    monkeypatch.setattr("app.main.verify_database_connection", verify_mock)
    monkeypatch.setattr("app.main.ensure_superuser", ensure_superuser_mock)
    monkeypatch.setattr("app.main.SessionLocal", lambda: session_mock)

    with TestClient(app):
        pass

    verify_mock.assert_called_once()
    ensure_superuser_mock.assert_called_once()
    session_mock.close.assert_called_once()
