"""Tests for user-related repositories."""

from unittest.mock import MagicMock

import pytest

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.users.role import RoleRepository
from app.repositories.users.user import UserRepository
from app.repositories.users.user_role import UserRoleRepository


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def user_repository(session):
    return UserRepository(session)


def test_user_repository_binds_user_model(session):
    assert UserRepository(session).model is User


def test_role_repository_binds_role_model(session):
    assert RoleRepository(session).model is Role


def test_user_role_repository_binds_user_role_model(session):
    assert UserRoleRepository(session).model is UserRole


def test_get_by_email_returns_user(session, user_repository):
    user = User(
        id=1, email="alice@example.com", password_hash="hash", full_name="Alice", is_active=True
    )
    session.scalar.return_value = user

    result = user_repository.get_by_email("alice@example.com")

    assert result is user
    session.scalar.assert_called_once()


def test_get_by_email_returns_none_when_missing(session, user_repository):
    session.scalar.return_value = None

    result = user_repository.get_by_email("missing@example.com")

    assert result is None
    session.scalar.assert_called_once()


def test_get_with_roles_returns_user(session, user_repository):
    user = MagicMock()
    session.scalar.return_value = user

    result = user_repository.get_with_roles(1)

    assert result is user
    session.scalar.assert_called_once()


def test_get_with_roles_returns_none_when_missing(session, user_repository):
    session.scalar.return_value = None

    result = user_repository.get_with_roles(999)

    assert result is None


def test_get_role_names_for_user_returns_global_roles(session, user_repository):
    session.scalars.return_value.all.return_value = ["Admin", "Farm Manager"]

    result = user_repository.get_role_names_for_user(1)

    assert result == ["Admin", "Farm Manager"]
    session.scalars.assert_called_once()


def test_get_role_names_for_user_returns_empty_list(session, user_repository):
    session.scalars.return_value.all.return_value = []

    assert user_repository.get_role_names_for_user(1) == []


def test_get_user_assignments_returns_role_and_farm_pairs(session, user_repository):
    session.execute.return_value.all.return_value = [
        ("Farm Manager", 5),
        ("Operations Team", 7),
    ]

    result = user_repository.get_user_assignments(1)

    assert result == [("Farm Manager", 5), ("Operations Team", 7)]
    session.execute.assert_called_once()


def test_get_user_assignments_returns_empty_list(session, user_repository):
    session.execute.return_value.all.return_value = []

    assert user_repository.get_user_assignments(1) == []


def test_role_repository_get_by_name_returns_role(session):
    role = Role(id=3, name="Admin", description="Administrator")
    session.scalar.return_value = role
    repository = RoleRepository(session)

    result = repository.get_by_name("Admin")

    assert result is role
    session.scalar.assert_called_once()


def test_role_repository_get_by_name_returns_none(session):
    session.scalar.return_value = None
    repository = RoleRepository(session)

    assert repository.get_by_name("Missing") is None
