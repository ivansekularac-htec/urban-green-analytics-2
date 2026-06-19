"""Unit tests for the role and farm-scope authorization helpers."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.security.dependencies import (
    assert_farm_access,
    assert_farm_in_scope,
    get_accessible_farm_ids,
    require_roles,
)
from app.security.roles import RoleName


def make_user(roles):
    """Build a minimal stub user where ``roles`` is ``[(RoleName, farm_id), ...]``."""
    return SimpleNamespace(
        id=1,
        is_active=True,
        user_roles=[
            SimpleNamespace(role=SimpleNamespace(name=role.value), farm_id=farm_id)
            for role, farm_id in roles
        ],
    )


# ---------------------------------------------------------------------
# require_roles
# ---------------------------------------------------------------------


def test_require_roles_allows_matching_role():
    user = make_user([(RoleName.ADMIN, None)])
    dep = require_roles(RoleName.ADMIN)

    assert dep(user) is user


def test_require_roles_allows_any_of_multiple():
    user = make_user([(RoleName.OPERATIONS_TEAM, 1)])
    dep = require_roles(RoleName.ADMIN, RoleName.OPERATIONS_TEAM)

    assert dep(user) is user


def test_require_roles_denies_when_no_match():
    user = make_user([(RoleName.FARM_MANAGER, 1)])
    dep = require_roles(RoleName.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        dep(user)

    assert exc_info.value.status_code == 403


def test_require_roles_denies_user_with_no_roles():
    user = make_user([])
    dep = require_roles(RoleName.ADMIN)

    with pytest.raises(HTTPException) as exc_info:
        dep(user)

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------
# get_accessible_farm_ids
# ---------------------------------------------------------------------


def test_get_accessible_farm_ids_returns_none_for_admin():
    user = make_user([(RoleName.ADMIN, None)])

    assert get_accessible_farm_ids(user) is None


def test_get_accessible_farm_ids_returns_farms_for_farm_manager():
    user = make_user([(RoleName.FARM_MANAGER, 1), (RoleName.FARM_MANAGER, 2)])

    assert get_accessible_farm_ids(user) == {1, 2}


def test_get_accessible_farm_ids_returns_empty_set_for_unscoped_non_admin():
    user = make_user([(RoleName.FARM_MANAGER, None)])

    assert get_accessible_farm_ids(user) == set()


# ---------------------------------------------------------------------
# assert_farm_access
# ---------------------------------------------------------------------


def test_assert_farm_access_admin_bypasses_check():
    user = make_user([(RoleName.ADMIN, None)])

    # Even on a farm the user has no scoped role for, Admin passes.
    assert_farm_access(user, farm_id=999, allowed_roles=(RoleName.OPERATIONS_TEAM,))


def test_assert_farm_access_allows_user_with_role_on_farm():
    user = make_user([(RoleName.OPERATIONS_TEAM, 1)])

    assert_farm_access(user, farm_id=1, allowed_roles=(RoleName.OPERATIONS_TEAM,))


def test_assert_farm_access_denies_user_with_role_on_other_farm():
    user = make_user([(RoleName.OPERATIONS_TEAM, 1)])

    with pytest.raises(HTTPException) as exc_info:
        assert_farm_access(user, farm_id=2, allowed_roles=(RoleName.OPERATIONS_TEAM,))

    assert exc_info.value.status_code == 403


def test_assert_farm_access_denies_user_with_wrong_role_on_correct_farm():
    user = make_user([(RoleName.FARM_MANAGER, 1)])

    with pytest.raises(HTTPException) as exc_info:
        assert_farm_access(user, farm_id=1, allowed_roles=(RoleName.OPERATIONS_TEAM,))

    assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------
# assert_farm_in_scope
# ---------------------------------------------------------------------


def test_assert_farm_in_scope_no_op_for_admin():
    assert_farm_in_scope(farm_id=42, farms=None)


def test_assert_farm_in_scope_allows_in_scope_farm():
    assert_farm_in_scope(farm_id=1, farms={1, 2})


def test_assert_farm_in_scope_hides_out_of_scope_farm_as_404():
    with pytest.raises(HTTPException) as exc_info:
        assert_farm_in_scope(farm_id=99, farms={1, 2})

    assert exc_info.value.status_code == 404
