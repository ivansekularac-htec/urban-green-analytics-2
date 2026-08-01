"""Tests for the demo user bootstrap helper."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.config import Settings
from app.security.password import verify_password
from app.seed.demo_users import ensure_demo_users


def _settings() -> Settings:
    return Settings()


def _db_returning(*values):
    """Return successive values from scalars().one_or_none()."""
    db = MagicMock(spec=Session)
    db.scalars.return_value.one_or_none.side_effect = values
    return db


def test_ensure_demo_users_creates_missing_users():
    settings = _settings()

    farm_manager_role = SimpleNamespace(id=1, name="FarmManager")
    operations_role = SimpleNamespace(id=2, name="OperationsTeam")

    db = _db_returning(
        None,
        farm_manager_role,
        None,
        operations_role,
    )

    next_user_id = 1

    def assign_id_on_flush():
        nonlocal next_user_id

        added = [call.args[0] for call in db.add.call_args_list]

        user = added[-1]

        if getattr(user, "id", None) is None:
            user.id = next_user_id
            next_user_id += 1

    db.flush.side_effect = assign_id_on_flush

    ensure_demo_users(db, settings)

    users = [call.args[0] for call in db.add.call_args_list if hasattr(call.args[0], "email")]

    assert len(users) == 2

    assert users[0].email == settings.demo_farm_manager_email
    assert verify_password(
        settings.demo_farm_manager_password,
        users[0].password_hash,
    )

    assert users[1].email == settings.demo_operations_email
    assert verify_password(
        settings.demo_operations_password,
        users[1].password_hash,
    )

    assignments = [
        call.args[0] for call in db.add.call_args_list if hasattr(call.args[0], "role_id")
    ]

    farm_manager_assignments = [
        assignment for assignment in assignments if assignment.role_id == farm_manager_role.id
    ]

    operations_assignments = [
        assignment for assignment in assignments if assignment.role_id == operations_role.id
    ]

    assert len(farm_manager_assignments) == 1
    assert farm_manager_assignments[0].farm_id == 1

    assert len(operations_assignments) == 15
    assert {assignment.farm_id for assignment in operations_assignments} == set(range(1, 16))

    assert db.commit.call_count == 2


def test_ensure_demo_users_is_idempotent():
    settings = _settings()

    farm_manager = SimpleNamespace(
        id=1,
        email=settings.demo_farm_manager_email,
    )

    operations = SimpleNamespace(
        id=2,
        email=settings.demo_operations_email,
    )

    db = _db_returning(
        farm_manager,
        operations,
    )

    ensure_demo_users(db, settings)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_demo_users_skips_when_role_missing():
    settings = _settings()

    db = _db_returning(
        None,  # farm manager user does not exist
        None,  # farm manager role missing
        None,  # operations user does not exist
        None,  # operations role missing
    )

    ensure_demo_users(db, settings)

    db.add.assert_not_called()
    db.commit.assert_not_called()
