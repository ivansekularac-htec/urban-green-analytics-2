"""Tests for auth router endpoints."""

from unittest.mock import MagicMock

import pytest

from app.main import app
from app.routers.v1.auth.auth import get_auth_service
from app.schemas.auth.auth import TokenResponse


@pytest.fixture
def auth_service():
    service = MagicMock()
    app.dependency_overrides[get_auth_service] = lambda: service
    return service


LOGIN_FORM = {
    "username": "alice@example.com",
    "password": "hunter2hunter2",
}


def test_login_returns_token_response(client, auth_service):
    auth_service.login.return_value = TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=900,
    )

    response = client.post("/api/v1/auth/login", data=LOGIN_FORM)

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
        data={"username": "alice@example.com", "password": "short"},
    )

    assert response.status_code == 422
    auth_service.login.assert_not_called()
