"""
test_auth_service.py
Tests for authentication service.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.schemas.auth import RegisterRequest, Token
from app.services.auth_service import AuthService


def make_user(
    user_id: int = 1,
    email: str = "admin@example.com",
    password_hash: str = "hashed-password",
    is_active: bool = True,
):
    user = MagicMock()
    user.id = user_id
    user.email = email
    user.password_hash = password_hash
    user.is_active = is_active

    return user


def test_register_user_success():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    created_user = make_user()

    service.user_repository.get_by_email.return_value = None
    service.user_repository.create.return_value = created_user

    register_data = RegisterRequest(
        email="admin@example.com",
        full_name="Admin User",
        password="password123",
    )

    with (
        patch(
            "app.services.auth_service.hash_password",
            return_value="hashed-password",
        ),
        patch(
            "app.services.auth_service.create_access_token",
            return_value="token-value",
        ),
    ):
        response = service.register_user(register_data)

    assert response.access_token == "token-value"


def test_register_user_integrity_error_raises_409():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    service.user_repository.get_by_email.return_value = None
    service.user_repository.create.side_effect = IntegrityError(
        statement="insert",
        params={},
        orig=Exception("duplicate"),
    )

    register_data = RegisterRequest(
        email="admin@example.com",
        full_name="Admin User",
        password="password123",
    )

    with (
        patch("app.services.auth_service.hash_password", return_value="hashed-password"),
        pytest.raises(HTTPException) as exc_info,
    ):
        service.register_user(register_data)

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "User with this email already exists."
    service.user_repository.rollback.assert_called_once()


def test_login_user_success():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    user = make_user()

    service.user_repository.get_by_email.return_value = user
    service.user_repository.get_role_names.return_value = ["ADMIN"]

    with (
        patch("app.services.auth_service.verify_password", return_value=True),
        patch("app.services.auth_service.create_access_token", return_value="token-value"),
    ):
        response = service.login_user(
            email="admin@example.com",
            password="password123",
        )

    assert isinstance(response, Token)
    assert response.access_token == "token-value"
    assert response.token_type == "bearer"

    service.user_repository.get_by_email.assert_called_once_with("admin@example.com")
    service.user_repository.get_role_names.assert_called_once_with(user.id)


def test_login_user_missing_user_raises_401():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    service.user_repository.get_by_email.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        service.login_user(
            email="missing@example.com",
            password="password123",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password."


def test_login_user_invalid_password_raises_401():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    service.user_repository.get_by_email.return_value = make_user()

    with (
        patch("app.services.auth_service.verify_password", return_value=False),
        pytest.raises(HTTPException) as exc_info,
    ):
        service.login_user(
            email="admin@example.com",
            password="wrongpassword",
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid email or password."


def test_login_user_inactive_user_raises_403():
    db = MagicMock()

    service = AuthService(db)
    service.user_repository = MagicMock()

    service.user_repository.get_by_email.return_value = make_user(is_active=False)

    with (
        patch("app.services.auth_service.verify_password", return_value=True),
        pytest.raises(HTTPException) as exc_info,
    ):
        service.login_user(
            email="admin@example.com",
            password="password123",
        )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user account."
