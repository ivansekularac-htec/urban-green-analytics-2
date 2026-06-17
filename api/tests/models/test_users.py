"""Tests for the user, role, and user-role ORM models."""

from app.models.users.role import Role
from app.models.users.user import User
from app.models.users.user_roles import UserRole


def test_user_assigns_fields():
    user = User(
        id=1,
        email="alice@example.com",
        password_hash="hash",
        full_name="Alice",
        is_active=True,
    )

    assert user.email == "alice@example.com"
    assert user.password_hash == "hash"
    assert user.full_name == "Alice"
    assert user.is_active is True


def test_role_assigns_fields():
    role = Role(id=1, name="Admin", description="Administrator")

    assert role.name == "Admin"
    assert role.description == "Administrator"


def test_user_role_assigns_fields():
    user_role = UserRole(id=1, user_id=2, role_id=3, farm_id=4)

    assert user_role.user_id == 2
    assert user_role.role_id == 3
    assert user_role.farm_id == 4


def test_user_role_links_user_and_role():
    user = User(id=1, email="a@b.c", password_hash="x", full_name="A", is_active=True)
    role = Role(id=1, name="Admin")
    user_role = UserRole(id=1, user_id=1, role_id=1, farm_id=None)

    user_role.user = user
    user_role.role = role

    assert user_role.user is user
    assert user_role.role is role
    assert user_role.farm_id is None
