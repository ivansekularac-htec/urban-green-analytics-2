"""
test_auth.py
Tests for authentication and authorization dependencies.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from jose import JWTError

from app.dependencies.auth import (
    ADMIN_ROLE,
    FARM_MANAGER_ROLE,
    OPERATIONS_ROLE,
    get_current_user,
    get_managed_farm_ids,
    require_farm_access,
    require_roles,
    user_has_farm_access,
    user_has_role,
)


def make_user(
    role_name: str | None = ADMIN_ROLE,
    farm_id: int | None = None,
    is_active: bool = True,
):
    user = MagicMock()
    user.id = 1
    user.is_active = is_active

    if role_name is None:
        user.user_roles = []
        return user

    role = MagicMock()
    role.name = role_name

    user_role = MagicMock()
    user_role.role = role
    user_role.farm_id = farm_id

    user.user_roles = [user_role]

    return user


def test_get_current_user_success():
    db = MagicMock()
    user = make_user()

    with (
        patch(
            "app.dependencies.auth.decode_access_token",
            return_value={"sub": "1"},
        ),
        patch("app.dependencies.auth.UserRepository") as repository_class,
    ):
        repository = MagicMock()
        repository.get.return_value = user
        repository_class.return_value = repository

        result = get_current_user(
            token="valid-token",
            db=db,
        )

    assert result == user
    repository.get.assert_called_once_with(1)


def test_get_current_user_missing_sub_raises_401():
    db = MagicMock()

    with (
        patch(
            "app.dependencies.auth.decode_access_token",
            return_value={},
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        get_current_user(
            token="invalid-token",
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_token_raises_401():
    db = MagicMock()

    with (
        patch(
            "app.dependencies.auth.decode_access_token",
            side_effect=JWTError("invalid token"),
        ),
        pytest.raises(HTTPException) as exc_info,
    ):
        get_current_user(
            token="invalid-token",
            db=db,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_missing_user_raises_401():
    db = MagicMock()

    with (
        patch(
            "app.dependencies.auth.decode_access_token",
            return_value={"sub": "1"},
        ),
        patch("app.dependencies.auth.UserRepository") as repository_class,
    ):
        repository = MagicMock()
        repository.get.return_value = None
        repository_class.return_value = repository

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                token="valid-token",
                db=db,
            )

    assert exc_info.value.status_code == 401


def test_get_current_user_inactive_user_raises_403():
    db = MagicMock()
    user = make_user(is_active=False)

    with (
        patch(
            "app.dependencies.auth.decode_access_token",
            return_value={"sub": "1"},
        ),
        patch("app.dependencies.auth.UserRepository") as repository_class,
    ):
        repository = MagicMock()
        repository.get.return_value = user
        repository_class.return_value = repository

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                token="valid-token",
                db=db,
            )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Inactive user account."


def test_require_roles_allows_admin():
    user = make_user(role_name=ADMIN_ROLE)

    checker = require_roles(OPERATIONS_ROLE)

    assert checker(user) == user


def test_require_roles_allows_allowed_role():
    user = make_user(role_name=OPERATIONS_ROLE)

    checker = require_roles(OPERATIONS_ROLE)

    assert checker(user) == user


def test_require_roles_rejects_missing_role():
    user = make_user(role_name=FARM_MANAGER_ROLE)

    checker = require_roles(OPERATIONS_ROLE)

    with pytest.raises(HTTPException) as exc_info:
        checker(user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions."


def test_user_has_role_returns_true_for_matching_role():
    user = make_user(role_name=FARM_MANAGER_ROLE)

    assert user_has_role(user, FARM_MANAGER_ROLE) is True


def test_user_has_role_returns_false_for_missing_role():
    user = make_user(role_name=OPERATIONS_ROLE)

    assert user_has_role(user, FARM_MANAGER_ROLE) is False


def test_user_has_farm_access_allows_admin():
    user = make_user(role_name=ADMIN_ROLE)

    assert user_has_farm_access(user, farm_id=10) is True


def test_user_has_farm_access_allows_manager_for_matching_farm():
    user = make_user(
        role_name=FARM_MANAGER_ROLE,
        farm_id=10,
    )

    assert user_has_farm_access(user, farm_id=10) is True


def test_user_has_farm_access_rejects_manager_for_other_farm():
    user = make_user(
        role_name=FARM_MANAGER_ROLE,
        farm_id=10,
    )

    assert user_has_farm_access(user, farm_id=20) is False


def test_require_farm_access_allows_matching_farm():
    user = make_user(
        role_name=FARM_MANAGER_ROLE,
        farm_id=10,
    )

    require_farm_access(user, farm_id=10)


def test_require_farm_access_rejects_missing_farm_access():
    user = make_user(
        role_name=FARM_MANAGER_ROLE,
        farm_id=10,
    )

    with pytest.raises(HTTPException) as exc_info:
        require_farm_access(user, farm_id=20)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Insufficient permissions for this farm."


def test_get_managed_farm_ids_returns_only_manager_farms():
    user = make_user(
        role_name=FARM_MANAGER_ROLE,
        farm_id=10,
    )

    assert get_managed_farm_ids(user) == [10]
