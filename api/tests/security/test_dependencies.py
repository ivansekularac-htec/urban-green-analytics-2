"""Tests for auth dependencies."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, status

from app.security.dependencies import get_current_user, require_roles
from app.security.jwt import create_access_token, create_refresh_token


def _active_user(user_id: int = 1):
    user = MagicMock()
    user.id = user_id
    user.is_active = True
    return user


def test_get_current_user_returns_active_user():
    token = create_access_token(
        user_id=1,
        email="alice@example.com",
        roles=["admin"],
    )
    db = MagicMock()
    user = _active_user()
    with patch("app.security.dependencies.UserRepository") as repo_cls:
        repo_cls.return_value.get.return_value = user
        result = get_current_user(token=token, db=db)
    assert result is user


def test_get_current_user_rejects_missing_token_user():
    token = create_access_token(
        user_id=1,
        email="alice@example.com",
        roles=["admin"],
    )
    db = MagicMock()
    with patch("app.security.dependencies.UserRepository") as repo_cls:
        repo_cls.return_value.get.return_value = None
        with pytest.raises(HTTPException) as exc:
            get_current_user(token=token, db=db)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_refresh_token():
    token = create_refresh_token(user_id=1)
    db = MagicMock()
    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=db)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="not-a-real-token", db=MagicMock())
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_require_roles_allows_matching_role():
    checker = require_roles("admin")
    current_user = _active_user()
    db = MagicMock()
    with patch("app.security.dependencies.UserRepository") as repo_cls:
        repo_cls.return_value.get_role_names_for_user.return_value = ["admin"]
        result = checker(current_user=current_user, db=db)
    assert result is current_user


def test_require_roles_rejects_missing_role():
    checker = require_roles("admin")
    current_user = _active_user()
    db = MagicMock()
    with patch("app.security.dependencies.UserRepository") as repo_cls:
        repo_cls.return_value.get_role_names_for_user.return_value = ["viewer"]
        with pytest.raises(HTTPException) as exc:
            checker(current_user=current_user, db=db)
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc.value.detail == "Insufficient permissions."
