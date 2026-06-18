"""Tests for the authentication service."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.password import hash_password
from app.services.auth.auth import AuthService

_EMAIL = "admin@uga.com"
_PASSWORD = "secret123"


def _fake_user(*, is_active: bool = True, role_names=("Admin",)):
    user = MagicMock()
    user.id = 1
    user.email = _EMAIL
    user.password_hash = hash_password(_PASSWORD)
    user.is_active = is_active

    user_roles = []
    for name in role_names:
        role = MagicMock()
        role.name = name
        user_role = MagicMock()
        user_role.role = role
        user_roles.append(user_role)
    user.user_roles = user_roles

    return user


# ------------------------------------------------------
# authenticate
# ------------------------------------------------------


def test_authenticate_success_returns_user():
    repo = MagicMock()
    repo.get_by_email.return_value = _fake_user()

    user = AuthService(repo).authenticate(_EMAIL, _PASSWORD)

    assert user.email == _EMAIL
    repo.get_by_email.assert_called_once_with(_EMAIL)


def test_authenticate_unknown_email_raises_401():
    repo = MagicMock()
    repo.get_by_email.return_value = None

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).authenticate("nobody@uga.com", _PASSWORD)

    assert exc.value.status_code == 401


def test_authenticate_wrong_password_raises_401():
    repo = MagicMock()
    repo.get_by_email.return_value = _fake_user()

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).authenticate(_EMAIL, "wrong-password")

    assert exc.value.status_code == 401


def test_authenticate_inactive_user_raises_401():
    repo = MagicMock()
    repo.get_by_email.return_value = _fake_user(is_active=False)

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).authenticate(_EMAIL, _PASSWORD)

    assert exc.value.status_code == 401


# ------------------------------------------------------
# login
# ------------------------------------------------------


def test_login_returns_token_pair_with_roles():
    repo = MagicMock()
    repo.get_by_email.return_value = _fake_user(role_names=("Admin", "Farm Manager"))

    response = AuthService(repo).login(_EMAIL, _PASSWORD)

    assert response.token_type == "bearer"
    assert response.expires_in == 30 * 60
    assert response.refresh_token

    claims = decode_token(response.access_token)
    assert claims["sub"] == "1"
    assert claims["email"] == _EMAIL
    assert claims["roles"] == ["Admin", "Farm Manager"]


# ------------------------------------------------------
# refresh
# ------------------------------------------------------


def test_refresh_returns_new_token_pair():
    repo = MagicMock()
    repo.get.return_value = _fake_user(role_names=("Admin",))

    response = AuthService(repo).refresh(create_refresh_token(user_id=1))

    repo.get.assert_called_once_with(1)
    assert response.refresh_token
    claims = decode_token(response.access_token)
    assert claims["roles"] == ["Admin"]


def test_refresh_rejects_access_token():
    repo = MagicMock()
    access = create_access_token(user_id=1, email=_EMAIL, roles=[])

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).refresh(access)

    assert exc.value.status_code == 401
    repo.get.assert_not_called()


def test_refresh_rejects_invalid_token():
    repo = MagicMock()

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).refresh("not-a-jwt")

    assert exc.value.status_code == 401


def test_refresh_rejects_inactive_user():
    repo = MagicMock()
    repo.get.return_value = _fake_user(is_active=False)

    with pytest.raises(HTTPException) as exc:
        AuthService(repo).refresh(create_refresh_token(user_id=1))

    assert exc.value.status_code == 401
