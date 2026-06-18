"""Tests for the authentication dependencies."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.security.dependencies import get_current_active_user, get_current_user
from app.security.jwt import create_access_token, create_refresh_token


def _db_returning(user):
    db = MagicMock()
    db.get.return_value = user
    return db


def test_get_current_user_returns_user_for_valid_token():
    fake_user = SimpleNamespace(id=1, is_active=True)
    token = create_access_token(user_id=1, email="a@uga.com", roles=[])

    user = get_current_user(token=token, db=_db_returning(fake_user))

    assert user is fake_user


def test_get_current_user_rejects_invalid_token():
    with pytest.raises(HTTPException) as exc:
        get_current_user(token="not-a-jwt", db=_db_returning(None))

    assert exc.value.status_code == 401


def test_get_current_user_rejects_refresh_token():
    refresh = create_refresh_token(user_id=1)

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=refresh, db=_db_returning(SimpleNamespace(id=1)))

    assert exc.value.status_code == 401


def test_get_current_user_rejects_unknown_user():
    token = create_access_token(user_id=999, email="ghost@uga.com", roles=[])

    with pytest.raises(HTTPException) as exc:
        get_current_user(token=token, db=_db_returning(None))

    assert exc.value.status_code == 401


def test_get_current_active_user_allows_active():
    user = SimpleNamespace(is_active=True)

    assert get_current_active_user(current_user=user) is user


def test_get_current_active_user_rejects_inactive():
    user = SimpleNamespace(is_active=False)

    with pytest.raises(HTTPException) as exc:
        get_current_active_user(current_user=user)

    assert exc.value.status_code == 403
