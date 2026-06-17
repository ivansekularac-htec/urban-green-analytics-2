"""Tests for user, role, and user-role schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.users.role import RoleCreate, RoleResponse, RoleUpdate
from app.schemas.users.user import (
    UserCreate,
    UserPasswordUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.users.user_roles import (
    UserRoleCreate,
    UserRoleResponse,
    UserRoleUpdate,
)


def test_user_create_accepts_valid_payload():
    create = UserCreate(
        email="alice@example.com",
        full_name="Alice",
        is_active=True,
        password="supersecret",
    )

    assert create.email == "alice@example.com"
    assert create.password == "supersecret"


def test_user_create_rejects_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", full_name="A", password="supersecret")


def test_user_create_rejects_short_password():
    with pytest.raises(ValidationError):
        UserCreate(email="a@b.c", full_name="A", password="short")


def test_user_update_accepts_partial_payload():
    update = UserUpdate(full_name="Alice B.", is_active=False)

    assert update.full_name == "Alice B."
    assert update.is_active is False
    assert update.email is None


def test_user_password_update_enforces_minimum_length():
    UserPasswordUpdate(password="goodpassword")

    with pytest.raises(ValidationError):
        UserPasswordUpdate(password="short")


def test_user_response_round_trip():
    response = UserResponse(
        id=1,
        email="alice@example.com",
        full_name="Alice",
        is_active=True,
        created_at=1,
        updated_at=2,
    )

    assert response.id == 1


def test_role_create_update_response():
    create = RoleCreate(name="Admin", description="Administrator")
    update = RoleUpdate(description="Updated")
    response = RoleResponse(
        id=1,
        name="Admin",
        description="Administrator",
        created_at=1,
        updated_at=2,
    )

    assert create.name == "Admin"
    assert update.description == "Updated"
    assert response.id == 1


def test_user_role_create_update_response():
    create = UserRoleCreate(user_id=1, role_id=2, farm_id=3)
    update = UserRoleUpdate(role_id=99)
    response = UserRoleResponse(
        id=1,
        user_id=1,
        role_id=2,
        farm_id=3,
        created_at=1,
        updated_at=2,
    )

    assert create.user_id == 1
    assert update.role_id == 99
    assert response.id == 1
