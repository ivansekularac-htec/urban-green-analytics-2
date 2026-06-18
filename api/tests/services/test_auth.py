"""Tests for AuthService."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.repositories.users.user import UserRepository
from app.schemas.auth.auth import LoginRequest
from app.security.jwt import create_refresh_token, decode_token
from app.security.password import hash_password
from app.security.roles import RoleName
from app.services.auth.auth import AuthService
from app.services.users.user import UserService


@pytest.fixture
def repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def user_service(repository):
    return MagicMock(spec=UserService)


@pytest.fixture
def service(repository, user_service):
    return AuthService(repository, user_service)


def _user(*, active: bool = True):
    user = MagicMock()
    user.id = 1
    user.email = "alice@example.com"
    user.is_active = active
    user.password_hash = hash_password("hunter2hunter2")
    return user


def test_login_returns_tokens_for_valid_credentials(service, repository):
    repository.get_by_email.return_value = _user()
    repository.get_role_names_for_user.return_value = [RoleName.ADMIN]

    result = service.login(LoginRequest(email="alice@example.com", password="hunter2hunter2"))

    assert result.token_type == "bearer"
    assert result.access_token
    assert result.refresh_token
    assert result.expires_in == 15 * 60

    access_payload = decode_token(result.access_token)
    assert access_payload["sub"] == "1"
    assert access_payload["roles"] == [RoleName.ADMIN]
    assert access_payload["type"] == "access"


def test_login_rejects_unknown_email(service, repository):
    repository.get_by_email.return_value = None

    with pytest.raises(HTTPException) as exc:
        service.login(LoginRequest(email="alice@example.com", password="hunter2hunter2"))

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Incorrect email or password."


def test_login_rejects_wrong_password(service, repository):
    repository.get_by_email.return_value = _user()

    with pytest.raises(HTTPException) as exc:
        service.login(LoginRequest(email="alice@example.com", password="wrong-password"))

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Incorrect email or password."


def test_login_rejects_inactive_user(service, repository):
    repository.get_by_email.return_value = _user(active=False)

    with pytest.raises(HTTPException) as exc:
        service.login(LoginRequest(email="alice@example.com", password="hunter2hunter2"))

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Inactive user."


def test_refresh_returns_new_tokens_for_valid_refresh_token(service, repository):
    user = _user()
    repository.get_with_roles.return_value = user
    repository.get_role_names_for_user.return_value = [RoleName.FARM_MANAGER]

    refresh_token = create_refresh_token(user_id=user.id)

    result = service.refresh(refresh_token)

    assert result.access_token
    assert result.refresh_token
    assert decode_token(result.access_token)["type"] == "access"


def test_refresh_rejects_access_token(service):
    from app.security.jwt import create_access_token

    token = create_access_token(
        user_id=1,
        email="alice@example.com",
        roles=[RoleName.ADMIN],
    )

    with pytest.raises(HTTPException) as exc:
        service.refresh(token)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid refresh token."


def test_refresh_rejects_missing_user(service, repository):
    refresh_token = create_refresh_token(user_id=999)
    repository.get_with_roles.return_value = None

    with pytest.raises(HTTPException) as exc:
        service.refresh(refresh_token)

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid refresh token."
