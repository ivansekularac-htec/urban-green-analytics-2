"""Tests for the superuser seeding routine."""

from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.security import superuser as superuser_module
from app.security.superuser import ensure_superuser


def _factory_for(db):
    @contextmanager
    def factory():
        yield db

    return factory


def test_skips_when_admin_role_missing():
    db = MagicMock()
    db.scalar.return_value = None  # no Admin role

    ensure_superuser(session_factory=_factory_for(db))

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_skips_when_superuser_already_exists():
    db = MagicMock()
    admin_role = SimpleNamespace(id=3, name="Admin")
    existing_user = SimpleNamespace(id=1)
    db.scalar.side_effect = [admin_role, existing_user]

    ensure_superuser(session_factory=_factory_for(db))

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_creates_superuser_and_assigns_admin_role():
    db = MagicMock()
    admin_role = SimpleNamespace(id=3, name="Admin")
    db.scalar.side_effect = [admin_role, None]  # role found, user missing

    ensure_superuser(session_factory=_factory_for(db))

    # one User add + one UserRole add
    assert db.add.call_count == 2
    db.commit.assert_called_once()

    added_user = db.add.call_args_list[0].args[0]
    assert added_user.email == superuser_module.get_settings().superuser_email
    assert added_user.is_active is True
