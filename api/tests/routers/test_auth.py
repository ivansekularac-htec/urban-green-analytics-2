"""Tests for the auth router (login, refresh, me).

The auth service and current-user dependency are overridden with mocks so no
database or credential verification runs here; service and dependency
behaviour are covered in tests/services and tests/security.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.main import app
from app.routers.v1.auth.auth import get_auth_service
from app.schemas.auth import TokenResponse
from app.security.dependencies import get_current_active_user

_LOGIN_PATH = "/api/v1/auth/login"
_REFRESH_PATH = "/api/v1/auth/refresh"
_ME_PATH = "/api/v1/auth/me"


def _token_pair():
    return TokenResponse(access_token="a.b.c", refresh_token="r.e.f", expires_in=1800)


# ------------------------------------------------------
# login
# ------------------------------------------------------


def test_login_success_returns_token_pair(client: TestClient):
    service = MagicMock()
    service.login.return_value = _token_pair()
    app.dependency_overrides[get_auth_service] = lambda: service

    response = client.post(
        _LOGIN_PATH,
        data={"username": "admin@uga.com", "password": "secret123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"] == "a.b.c"
    assert body["refresh_token"] == "r.e.f"
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 1800
    service.login.assert_called_once_with(email="admin@uga.com", password="secret123")


def test_login_invalid_credentials_returns_401(client: TestClient):
    service = MagicMock()
    service.login.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect email or password.",
    )
    app.dependency_overrides[get_auth_service] = lambda: service

    response = client.post(
        _LOGIN_PATH,
        data={"username": "admin@uga.com", "password": "wrong"},
    )

    assert response.status_code == 401


def test_login_requires_form_fields(client: TestClient):
    app.dependency_overrides[get_auth_service] = lambda: MagicMock()

    response = client.post(_LOGIN_PATH, data={})

    assert response.status_code == 422


# ------------------------------------------------------
# refresh
# ------------------------------------------------------


def test_refresh_success_returns_token_pair(client: TestClient):
    service = MagicMock()
    service.refresh.return_value = _token_pair()
    app.dependency_overrides[get_auth_service] = lambda: service

    response = client.post(_REFRESH_PATH, json={"refresh_token": "r.e.f"})

    assert response.status_code == 200
    assert response.json()["access_token"] == "a.b.c"
    service.refresh.assert_called_once_with("r.e.f")


def test_refresh_invalid_token_returns_401(client: TestClient):
    service = MagicMock()
    service.refresh.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token.",
    )
    app.dependency_overrides[get_auth_service] = lambda: service

    response = client.post(_REFRESH_PATH, json={"refresh_token": "bad"})

    assert response.status_code == 401


# ------------------------------------------------------
# me
# ------------------------------------------------------


def test_me_returns_current_user(client: TestClient):
    current = SimpleNamespace(
        id=1,
        email="admin@uga.com",
        full_name="Administrator",
        is_active=True,
        created_at=1,
        updated_at=2,
    )
    app.dependency_overrides[get_current_active_user] = lambda: current

    response = client.get(_ME_PATH)

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "admin@uga.com"
    assert body["id"] == 1


def test_me_without_token_returns_401(client: TestClient):
    # Remove the global admin override so the real dependency runs.
    app.dependency_overrides.pop(get_current_active_user, None)

    response = client.get(_ME_PATH)

    assert response.status_code == 401
