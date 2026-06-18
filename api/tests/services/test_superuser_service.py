"""
test_superuser_service.py
Tests for initial superuser seeding.
"""

from unittest.mock import MagicMock, patch

from app.services.superuser_service import ensure_superuser


def make_settings():
    settings = MagicMock()
    settings.superuser_email = "admin@example.com"
    settings.superuser_full_name = "System Admin"
    settings.superuser_password = "admin12345"

    return settings


def make_session_factory(db: MagicMock):
    session_context = MagicMock()
    session_context.__enter__.return_value = db
    session_context.__exit__.return_value = None

    session_factory = MagicMock(return_value=session_context)

    return session_factory


def test_ensure_superuser_skips_when_admin_role_missing():
    db = MagicMock()
    db.scalar.return_value = None

    session_factory = make_session_factory(db)

    with patch(
        "app.services.superuser_service.get_settings",
        return_value=make_settings(),
    ):
        ensure_superuser(session_factory=session_factory)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_superuser_skips_when_user_already_exists():
    db = MagicMock()

    admin_role = MagicMock()
    existing_user = MagicMock()

    db.scalar.side_effect = [
        admin_role,
        existing_user,
    ]

    session_factory = make_session_factory(db)

    with patch(
        "app.services.superuser_service.get_settings",
        return_value=make_settings(),
    ):
        ensure_superuser(session_factory=session_factory)

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_ensure_superuser_creates_user_and_assigns_admin_role():
    db = MagicMock()

    admin_role = MagicMock()
    admin_role.id = 1

    db.scalar.side_effect = [
        admin_role,
        None,
    ]

    session_factory = make_session_factory(db)

    with (
        patch(
            "app.services.superuser_service.get_settings",
            return_value=make_settings(),
        ),
        patch(
            "app.services.superuser_service.hash_password",
            return_value="hashed-password",
        ),
    ):
        ensure_superuser(session_factory=session_factory)

    assert db.add.call_count == 2
    db.flush.assert_called_once()
    db.commit.assert_called_once()

    created_user = db.add.call_args_list[0].args[0]
    created_user.id = 10

    created_user_role = db.add.call_args_list[1].args[0]

    assert created_user.email == "admin@example.com"
    assert created_user.full_name == "System Admin"
    assert created_user.password_hash == "hashed-password"
    assert created_user.is_active is True

    assert created_user_role.role_id == 1
    assert created_user_role.farm_id is None
