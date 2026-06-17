"""Tests for the FastAPI application entry point."""

from unittest.mock import patch

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
