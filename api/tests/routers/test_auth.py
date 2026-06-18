"""Tests for auth router endpoints."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.main import app
from app.routers.v1.auth.auth import get_auth_service
from app.schemas.auth.auth import TokenResponse
from tests.routers.conftest import client  # noqa: F401 - fixture from conftest


@pytest.fixture
def auth_service():
    return MagicMock()


@pytest.fixture(autouse=True)
def override_auth_service(auth_service):
    app.dependency_overrides[get_auth_service] = lambda: auth_service
    yield
    app.dependency_overrides.clear()


REGISTER_PAYLOAD = {
    "email": "alice@example.com",
    "full_name": "Alice",
    "password": "hunter2hunter2",
}
LOGIN_PAYLOAD = {
    "email": "alice@example.com",
    "password": "hunter2hunter2",
}


def test_register_returns_201(client, auth_service):
    auth_service.register.return_value = {
        **REGISTER_PAYLOAD,
        "id": 1,
        "is_active": True,
        "created_at": 1,
        "updated_at": 2,
    }
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    auth_service.register.assert_called_once()


def test_login_returns_token_response(client, auth_service):
    auth_service.login.return_value = TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=900,
    )
    response = client.post("/api/v1/auth/login", json=LOGIN_PAYLOAD)
    assert response.status_code == 200
    assert response.json() == {
        "access_token": "access-token",
        "refresh_token": "refresh-token",
        "token_type": "bearer",
        "expires_in": 900,
    }
    auth_service.login.assert_called_once()


def test_refresh_returns_token_response(client, auth_service):
    auth_service.refresh.return_value = TokenResponse(
        access_token="new-access",
        refresh_token="new-refresh",
        expires_in=900,
    )
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "old-refresh"},
    )
    assert response.status_code == 200
    auth_service.refresh.assert_called_once_with("old-refresh")


def test_login_validation_error_for_short_password(client, auth_service):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "short"},
    )
    assert response.status_code == 422
    auth_service.login.assert_not_called()


def test_register_maps_service_conflict_to_http_response(client, auth_service):
    auth_service.register.side_effect = HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Email already registered.",
    )
    response = client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered."
