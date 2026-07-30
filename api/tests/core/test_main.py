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
