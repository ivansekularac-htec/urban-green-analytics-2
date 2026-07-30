"""Tests for the demo user bootstrap helper.

Uses ``MagicMock`` for the SQLAlchemy session — same style as
``test_superuser.py``: logic only, no real database.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.models.users.user import User
from app.models.users.user_roles import UserRole
from app.security.demo_users import ensure_demo_users
from app.security.password import verify_password


def _settings(**overrides) -> Settings:
    # Keep ops farm list small so create-path mocks stay readable.
    base = {"demo_ops_farm_ids": "1,2,3"}
    base.update(overrides)
    return Settings().model_copy(update=base)


def _assign_user_ids_on_flush(db: MagicMock) -> None:
    """Emulate ORM populating ``User.id`` on flush."""

    next_id = 100

    def assign_id() -> None:
        nonlocal next_id
        for call in db.add.call_args_list:
            obj = call.args[0]
            if isinstance(obj, User) and obj.id is None:
                obj.id = next_id
                next_id += 1

    db.flush.side_effect = assign_id


def test_ensure_demo_users_creates_both_when_missing():
    settings = _settings()
    fm_role = SimpleNamespace(id=1, name="Farm Manager")
    ops_role = SimpleNamespace(id=2, name="Operations Team")
    farm = SimpleNamespace(id=1)

    db = MagicMock()
    # Call order inside ensure_demo_users:
    #   role FM, role Ops,
    #   manager lookup, farm 1,
    #   ops lookup, farm 1, farm 2, farm 3
    db.scalars.return_value.one_or_none.side_effect = [
        fm_role,
        ops_role,
        None,
        farm,
        None,
        farm,
        farm,
        farm,
    ]
    _assign_user_ids_on_flush(db)

    manager, ops = ensure_demo_users(db, settings)

    assert manager.email == settings.demo_farm_manager_email
    assert ops.email == settings.demo_ops_email
    assert verify_password(settings.demo_farm_manager_password, manager.password_hash)
    assert verify_password(settings.demo_ops_password, ops.password_hash)

    added = [call.args[0] for call in db.add.call_args_list]
    users = [obj for obj in added if isinstance(obj, User)]
    roles = [obj for obj in added if isinstance(obj, UserRole)]

    assert len(users) == 2
    assert len(roles) == 4  # manager: 1 farm, ops: 3 farms
    assert roles[0].role_id == fm_role.id
    assert roles[0].farm_id == settings.demo_farm_manager_farm_id
    assert {r.farm_id for r in roles[1:]} == {1, 2, 3}
    assert all(r.role_id == ops_role.id for r in roles[1:])
    assert db.commit.call_count == 2


def test_ensure_demo_users_is_idempotent_when_users_exist():
    settings = _settings()
    fm_role = SimpleNamespace(id=1, name="Farm Manager")
    ops_role = SimpleNamespace(id=2, name="Operations Team")
    existing_manager = SimpleNamespace(
        id=10, email=settings.demo_farm_manager_email, is_active=True
    )
    existing_ops = SimpleNamespace(id=11, email=settings.demo_ops_email, is_active=True)

    db = MagicMock()
    db.scalars.return_value.one_or_none.side_effect = [
        fm_role,
        ops_role,
        existing_manager,
        existing_ops,
    ]

    manager, ops = ensure_demo_users(db, settings)

    assert manager is existing_manager
    assert ops is existing_ops
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_demo_users_raises_when_farm_manager_role_missing():
    settings = _settings()
    db = MagicMock()
    db.scalars.return_value.one_or_none.return_value = None

    with pytest.raises(RuntimeError, match="Farm Manager"):
        ensure_demo_users(db, settings)


def test_ensure_demo_users_raises_when_farm_missing():
    settings = _settings(demo_ops_farm_ids="1")
    fm_role = SimpleNamespace(id=1, name="Farm Manager")
    ops_role = SimpleNamespace(id=2, name="Operations Team")

    db = MagicMock()
    # role FM, role Ops, manager lookup missing, farm lookup missing
    db.scalars.return_value.one_or_none.side_effect = [
        fm_role,
        ops_role,
        None,
        None,
    ]

    with pytest.raises(RuntimeError, match="farm_id=1"):
        ensure_demo_users(db, settings)
