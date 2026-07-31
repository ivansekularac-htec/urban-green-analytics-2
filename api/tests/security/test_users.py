"""Tests for the user bootstrap helper.

Uses ``MagicMock`` for the SQLAlchemy session — the goal is to verify
the logic without a real database, matching the superuser bootstrap tests.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session

from app.config import Settings
from app.security.password import verify_password
from app.security.roles import RoleName
from app.security.users import ensure_users


def _settings() -> Settings:
    # The conftest sets the user env vars before app modules import.
    return Settings()


def _db_returning(*values):
    """Stub consecutive ``scalars().one_or_none()`` results."""

    db = MagicMock(spec=Session)
    db.scalars.return_value.one_or_none.side_effect = values
    return db


def test_ensure_users_creates_users_when_missing():
    settings = _settings()

    manager_role = SimpleNamespace(
        id=2,
        name=RoleName.FARM_MANAGER.value,
    )
    operations_role = SimpleNamespace(
        id=3,
        name=RoleName.OPERATIONS_TEAM.value,
    )

    db = _db_returning(
        None,
        manager_role,
        None,
        operations_role,
    )

    user_ids = iter([41, 42])

    # ``flush`` would normally populate ``user.id``.
    def assign_id_on_flush():
        user = db.add.call_args.args[0]
        user.id = next(user_ids)

    db.flush.side_effect = assign_id_on_flush

    operations_farms = list(range(21, 36))

    with patch(
        "app.security.users._get_random_farm_ids",
        side_effect=[
            [11],
            operations_farms,
        ],
    ):
        manager, operations = ensure_users(db, settings)

    assert manager.email == settings.farm_manager_email
    assert manager.is_active is True
    assert verify_password(
        settings.farm_manager_password,
        manager.password_hash,
    )

    assert operations.email == settings.operations_team_email
    assert operations.is_active is True
    assert verify_password(
        settings.operations_team_password,
        operations.password_hash,
    )

    # Manager User, one assignment, Operations User, fifteen assignments.
    assert db.add.call_count == 18

    manager_assignment = db.add.call_args_list[1].args[0]
    assert manager_assignment.user_id == manager.id
    assert manager_assignment.role_id == manager_role.id
    assert manager_assignment.farm_id == 11

    operations_assignments = [call.args[0] for call in db.add.call_args_list[3:]]

    assert {assignment.farm_id for assignment in operations_assignments} == set(operations_farms)

    assert all(
        assignment.user_id == operations.id and assignment.role_id == operations_role.id
        for assignment in operations_assignments
    )

    assert db.commit.call_count == 2


def test_ensure_users_is_idempotent_when_users_exist():
    settings = _settings()

    existing_manager = SimpleNamespace(
        id=41,
        email=settings.farm_manager_email,
        is_active=True,
    )
    existing_operations = SimpleNamespace(
        id=42,
        email=settings.operations_team_email,
        is_active=True,
    )

    db = _db_returning(
        existing_manager,
        existing_operations,
    )

    manager, operations = ensure_users(db, settings)

    assert manager is existing_manager
    assert operations is existing_operations

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_users_skips_manager_when_role_is_missing():
    settings = _settings()

    operations_role = SimpleNamespace(
        id=3,
        name=RoleName.OPERATIONS_TEAM.value,
    )

    db = _db_returning(
        None,
        None,
        None,
        operations_role,
    )

    with patch(
        "app.security.users._get_random_farm_ids",
        return_value=list(range(1, 16)),
    ):
        manager, operations = ensure_users(db, settings)

    assert manager is None
    assert operations is not None
