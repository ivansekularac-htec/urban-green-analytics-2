"""Tests for user-related repositories."""

from unittest.mock import MagicMock

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.repositories.users.role import RoleRepository
from app.repositories.users.user import UserRepository
from app.repositories.users.user_role import UserRoleRepository


def test_user_repository_binds_user_model():
    assert UserRepository(MagicMock()).model is User


def test_role_repository_binds_role_model():
    assert RoleRepository(MagicMock()).model is Role


def test_user_role_repository_binds_user_role_model():
    assert UserRoleRepository(MagicMock()).model is UserRole
