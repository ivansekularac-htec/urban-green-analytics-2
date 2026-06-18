"""Tests for authentication router."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.routers.v1.auth.auth import login
from app.security.jwt import decode_access_token


def test_login_returns_access_token(monkeypatch):
    user = MagicMock()
    user.id = 1
    user.email = "admin@example.com"
    user.password_hash = "hashed-password"
    user.is_active = True

    role = MagicMock()
    role.name = "Admin"

    user_role = MagicMock()
    user_role.role = role
    user_role.farm_id = None

    user.user_roles = [user_role]

    db = MagicMock()
    db.scalar.return_value = user

    monkeypatch.setattr(
        "app.routers.v1.auth.auth.verify_password",
        lambda password, password_hash: True,
    )

    response = login(
        form_data=MagicMock(
            username="admin@example.com",
            password="admin12345",
        ),
        db=db,
    )

    assert response.token_type == "bearer"
    assert response.access_token

    payload = decode_access_token(response.access_token)

    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["email"] == "admin@example.com"
    assert payload["roles"] == ["Admin"]
    assert payload["farm_ids"] == []


def test_login_raises_401_for_unknown_user():
    db = MagicMock()
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        login(
            form_data=MagicMock(
                username="missing@example.com",
                password="admin12345",
            ),
            db=db,
        )

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid email or password"


def test_login_raises_401_for_inactive_user():
    user = MagicMock()
    user.is_active = False

    db = MagicMock()
    db.scalar.return_value = user

    with pytest.raises(HTTPException) as exc:
        login(
            form_data=MagicMock(
                username="inactive@example.com",
                password="admin12345",
            ),
            db=db,
        )

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid email or password"


def test_login_raises_401_for_invalid_password(monkeypatch):
    user = MagicMock()
    user.password_hash = "hashed-password"
    user.is_active = True

    db = MagicMock()
    db.scalar.return_value = user

    monkeypatch.setattr(
        "app.routers.v1.auth.auth.verify_password",
        lambda password, password_hash: False,
    )

    with pytest.raises(HTTPException) as exc:
        login(
            form_data=MagicMock(
                username="admin@example.com",
                password="wrong-password",
            ),
            db=db,
        )

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Invalid email or password"
