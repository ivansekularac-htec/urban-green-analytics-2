"""Tests for superuser bootstrap on application startup."""

from unittest.mock import MagicMock, patch

import pytest

from app.config import Settings
from app.security.roles import RoleName
from app.services.users.bootstrap import ensure_superuser


@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def settings():
    return Settings(
        postgres_user="test",
        postgres_password="test",
        postgres_host="localhost",
        postgres_port=5432,
        postgres_db="test",
        postgres_schema="app",
        jwt_secret_key="test-secret-key-for-tests-only",
        superuser_email="admin@example.com",
        superuser_password="hunter2hunter2",
        superuser_full_name="System Administrator",
    )


def test_ensure_superuser_skips_when_env_vars_missing(db):
    settings = MagicMock()
    settings.superuser_email = None
    settings.superuser_password = None

    with patch("app.services.users.bootstrap.UserRepository") as user_repo_cls:
        ensure_superuser(db, settings)

    user_repo_cls.assert_not_called()


def test_ensure_superuser_skips_when_user_already_exists(db, settings):
    with patch("app.services.users.bootstrap.UserRepository") as user_repo_cls:
        user_repo_cls.return_value.get_by_email.return_value = MagicMock()

        ensure_superuser(db, settings)

    user_repo_cls.return_value.get_by_email.assert_called_once_with(settings.superuser_email)
    user_repo_cls.return_value.create.assert_not_called()


@patch("app.services.users.bootstrap.UserRoleRepository")
@patch("app.services.users.bootstrap.RoleRepository")
@patch("app.services.users.bootstrap.UserService")
@patch("app.services.users.bootstrap.UserRepository")
def test_ensure_superuser_creates_user_and_admin_role(
    user_repo_cls,
    user_service_cls,
    role_repo_cls,
    user_role_repo_cls,
    db,
    settings,
):
    user_repo_cls.return_value.get_by_email.return_value = None

    created_user = MagicMock()
    created_user.id = 1
    user_service_cls.return_value.create.return_value = created_user

    admin_role = MagicMock()
    admin_role.id = 3
    role_repo_cls.return_value.get_by_name.return_value = admin_role

    ensure_superuser(db, settings)

    user_service_cls.return_value.create.assert_called_once()
    role_repo_cls.return_value.get_by_name.assert_called_once_with(RoleName.ADMIN)
    user_role_repo_cls.return_value.create.assert_called_once_with(
        {
            "user_id": 1,
            "role_id": 3,
            "farm_id": None,
        }
    )
    user_role_repo_cls.return_value.commit.assert_called_once()


@patch("app.services.users.bootstrap.RoleRepository")
@patch("app.services.users.bootstrap.UserService")
@patch("app.services.users.bootstrap.UserRepository")
def test_ensure_superuser_raises_when_admin_role_missing(
    user_repo_cls,
    user_service_cls,
    role_repo_cls,
    db,
    settings,
):
    user_repo_cls.return_value.get_by_email.return_value = None
    user_service_cls.return_value.create.return_value = MagicMock(id=1)
    role_repo_cls.return_value.get_by_name.return_value = None

    with pytest.raises(RuntimeError, match="Run database seed first"):
        ensure_superuser(db, settings)
