"""Tests for the bootstrap user helpers.

Uses ``MagicMock`` for the SQLAlchemy session to verify the bootstrap
logic without a real database.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.config import Settings
from app.security.password import verify_password
from app.security.roles import RoleName
from app.security.users import ensure_farm_manager, ensure_operations_user


def _settings() -> Settings:
    """Return application settings populated from test environment variables."""
    return Settings()


def _db_returning(*values):
    """Return a mocked session with consecutive ``one_or_none`` results."""

    db = MagicMock(spec=Session)
    db.scalars.return_value.one_or_none.side_effect = values
    return db


def test_ensure_farm_manager_creates_user_when_missing():
    """Create the farm manager when it does not already exist."""

    settings = _settings()

    manager_role = SimpleNamespace(
        id=2,
        name=RoleName.FARM_MANAGER.value,
    )

    db = _db_returning(
        None,
        manager_role,
    )

    def assign_id_on_flush():
        """Simulate SQLAlchemy assigning the primary key."""
        user = db.add.call_args.args[0]
        user.id = 41

    db.flush.side_effect = assign_id_on_flush

    manager = ensure_farm_manager(db, settings)

    assert manager.email == settings.farm_manager_email
    assert manager.full_name == settings.farm_manager_full_name
    assert manager.is_active is True
    assert verify_password(
        settings.farm_manager_password,
        manager.password_hash,
    )

    assignments = [call.args[0] for call in db.add.call_args_list[1:]]

    assert {assignment.farm_id for assignment in assignments} == set(settings.farm_manager_farm_ids)

    assert all(
        assignment.user_id == manager.id and assignment.role_id == manager_role.id
        for assignment in assignments
    )

    db.commit.assert_called_once()


def test_ensure_operations_user_creates_user_when_missing():
    """Create the operations user when it does not already exist."""

    settings = _settings()

    operations_role = SimpleNamespace(
        id=3,
        name=RoleName.OPERATIONS_TEAM.value,
    )

    db = _db_returning(
        None,
        operations_role,
    )

    def assign_id_on_flush():
        """Simulate SQLAlchemy assigning the primary key."""
        user = db.add.call_args.args[0]
        user.id = 42

    db.flush.side_effect = assign_id_on_flush

    operations = ensure_operations_user(db, settings)

    assert operations.email == settings.operations_email
    assert operations.full_name == settings.operations_full_name
    assert operations.is_active is True
    assert verify_password(
        settings.operations_password,
        operations.password_hash,
    )

    assignments = [call.args[0] for call in db.add.call_args_list[1:]]

    assert {assignment.farm_id for assignment in assignments} == set(settings.operations_farm_ids)

    assert all(
        assignment.user_id == operations.id and assignment.role_id == operations_role.id
        for assignment in assignments
    )

    db.commit.assert_called_once()


def test_ensure_farm_manager_is_idempotent_when_user_exists():
    """Return the existing farm manager without creating a new one."""

    settings = _settings()

    existing_manager = SimpleNamespace(
        id=41,
        email=settings.farm_manager_email,
        is_active=True,
    )

    db = _db_returning(existing_manager)

    manager = ensure_farm_manager(db, settings)

    assert manager is existing_manager

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_operations_user_is_idempotent_when_user_exists():
    """Return the existing operations user without creating a new one."""

    settings = _settings()

    existing_operations = SimpleNamespace(
        id=42,
        email=settings.operations_email,
        is_active=True,
    )

    db = _db_returning(existing_operations)

    operations = ensure_operations_user(db, settings)

    assert operations is existing_operations

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_farm_manager_raises_when_role_is_missing():
    """Raise an error when the farm manager role does not exist."""

    settings = _settings()

    db = _db_returning(
        None,
        None,
    )

    with pytest.raises(RuntimeError, match=rf"Role '{RoleName.FARM_MANAGER.value}' not found\."):
        ensure_farm_manager(db, settings)


def test_ensure_operations_user_raises_when_role_is_missing():
    """Raise an error when the operations role does not exist."""

    settings = _settings()

    db = _db_returning(
        None,
        None,
    )

    with pytest.raises(RuntimeError, match=rf"Role '{RoleName.OPERATIONS_TEAM.value}' not found\."):
        ensure_operations_user(db, settings)
