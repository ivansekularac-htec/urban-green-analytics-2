"""Tests for the demo user bootstrap helper.

Uses ``MagicMock(spec=Session)`` for the SQLAlchemy session — logic only,
no real database.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

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


def _stub_db(results: list) -> MagicMock:
    """Stub session.scalars() with a queue of return values.

    - list  -> result.all()
    - other -> result.one_or_none()
    """
    db = MagicMock(spec=Session)
    queue = iter(results)

    def scalars(_stmt):
        value = next(queue)
        result = MagicMock()
        if isinstance(value, list):
            result.all.return_value = value
            result.one_or_none.return_value = value[0] if value else None
        else:
            result.one_or_none.return_value = value
            result.all.return_value = [] if value is None else [value]
        return result

    db.scalars.side_effect = scalars
    return db


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

    # Per user: known farms (.all), then user lookup (one_or_none).
    db = _stub_db(
        [
            fm_role,
            [1],
            None,
            ops_role,
            [1, 2, 3],
            None,
        ]
    )
    _assign_user_ids_on_flush(db)

    ensure_demo_users(db, settings)

    added = [call.args[0] for call in db.add.call_args_list]
    users = [obj for obj in added if isinstance(obj, User)]
    roles = [obj for obj in added if isinstance(obj, UserRole)]

    assert len(users) == 2
    assert users[0].email == settings.demo_farm_manager_email
    assert users[1].email == settings.demo_ops_email
    assert verify_password(settings.demo_farm_manager_password, users[0].password_hash)
    assert verify_password(settings.demo_ops_password, users[1].password_hash)
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

    db = _stub_db(
        [
            fm_role,
            [1],
            existing_manager,
            [SimpleNamespace(farm_id=1)],
            ops_role,
            [1, 2, 3],
            existing_ops,
            [
                SimpleNamespace(farm_id=1),
                SimpleNamespace(farm_id=2),
                SimpleNamespace(farm_id=3),
            ],
        ]
    )

    ensure_demo_users(db, settings)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_demo_users_skips_when_role_missing():
    settings = _settings()
    db = _stub_db([None, None])

    ensure_demo_users(db, settings)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_demo_users_skips_missing_farms_without_raising():
    settings = _settings(demo_ops_farm_ids="1")
    fm_role = SimpleNamespace(id=1, name="Farm Manager")
    ops_role = SimpleNamespace(id=2, name="Operations Team")

    # Farms not in DB -> empty known lists; users are still created with no grants.
    db = _stub_db(
        [
            fm_role,
            [],
            None,
            ops_role,
            [],
            None,
        ]
    )
    _assign_user_ids_on_flush(db)

    ensure_demo_users(db, settings)

    added = [call.args[0] for call in db.add.call_args_list]
    users = [obj for obj in added if isinstance(obj, User)]
    roles = [obj for obj in added if isinstance(obj, UserRole)]
    assert len(users) == 2
    assert roles == []
    assert db.commit.call_count == 2


def test_ensure_demo_users_reconciles_farm_grants_when_config_drifts():
    settings = _settings(demo_ops_farm_ids="1,2,3")
    fm_role = SimpleNamespace(id=1, name="Farm Manager")
    ops_role = SimpleNamespace(id=2, name="Operations Team")
    existing_manager = SimpleNamespace(
        id=10, email=settings.demo_farm_manager_email, is_active=True
    )
    existing_ops = SimpleNamespace(id=11, email=settings.demo_ops_email, is_active=True)
    stale_ops_grant = SimpleNamespace(farm_id=1)

    db = _stub_db(
        [
            fm_role,
            [1],
            existing_manager,
            [SimpleNamespace(farm_id=1)],  # manager already correct
            ops_role,
            [1, 2, 3],
            existing_ops,
            [stale_ops_grant],  # missing farms 2 and 3
        ]
    )

    ensure_demo_users(db, settings)

    added_roles = [
        call.args[0] for call in db.add.call_args_list if isinstance(call.args[0], UserRole)
    ]
    assert {r.farm_id for r in added_roles} == {2, 3}
    assert all(r.role_id == ops_role.id for r in added_roles)
    assert all(r.user_id == existing_ops.id for r in added_roles)
    db.delete.assert_not_called()
    assert db.commit.call_count == 1
