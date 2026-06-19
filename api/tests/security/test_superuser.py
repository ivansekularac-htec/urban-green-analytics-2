"""Tests for the superuser bootstrap helper.

Uses ``MagicMock`` for the SQLAlchemy session — the goal is to verify
the *logic* (idempotency, role lookup, password hashing) without a real
database, matching the project's existing service/repository test style.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.config import Settings
from app.security.password import verify_password
from app.security.superuser import ensure_superuser


def _settings() -> Settings:
    # The conftest sets the SUPERUSER_* env vars before app modules import.
    return Settings()


def _db_returning(user, role):
    """Stub a session whose two ``scalars().one_or_none()`` calls return
    the given user and role in order."""
    db = MagicMock()
    db.scalars.return_value.one_or_none.side_effect = [user, role]
    return db


def test_ensure_superuser_creates_user_when_missing():
    settings = _settings()
    admin_role = SimpleNamespace(id=3, name="Admin")
    db = _db_returning(user=None, role=admin_role)

    # ``flush`` would normally populate ``user.id``; emulate that side effect.
    def assign_id_on_flush():
        added = [call.args[0] for call in db.add.call_args_list]
        if added and added[0].id is None:
            added[0].id = 42

    db.flush.side_effect = assign_id_on_flush

    user = ensure_superuser(db, settings)

    assert user.email == settings.superuser_email
    assert user.is_active is True
    assert verify_password(settings.superuser_password, user.password_hash)

    # Two add() calls: one for the User, one for the UserRole assignment.
    assert db.add.call_count == 2
    user_role = db.add.call_args_list[1].args[0]
    assert user_role.role_id == admin_role.id
    assert user_role.farm_id is None
    db.commit.assert_called_once()


def test_ensure_superuser_is_idempotent_when_user_exists():
    settings = _settings()
    existing = SimpleNamespace(id=42, email=settings.superuser_email, is_active=True)
    db = MagicMock()
    db.scalars.return_value.one_or_none.return_value = existing

    user = ensure_superuser(db, settings)

    assert user is existing
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_superuser_raises_when_admin_role_missing():
    settings = _settings()
    db = _db_returning(user=None, role=None)

    with pytest.raises(RuntimeError, match="Admin"):
        ensure_superuser(db, settings)
