"""Tests for user-related services.

``UserService`` overrides ``create`` and ``update`` to hash passwords, so
those are exercised in detail. ``RoleService`` and ``UserRoleService`` are
plain ``BaseService`` subclasses and only need an entity-name smoke test.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.repositories.users.user import UserRepository
from app.schemas.users.user import UserCreate, UserUpdate
from app.services.users.role import RoleService
from app.services.users.user import UserService
from app.services.users.user_role import UserRoleService


@pytest.fixture
def repository():
    return MagicMock(spec=UserRepository)


@pytest.fixture
def service(repository):
    return UserService(repository)


def _integrity_error() -> IntegrityError:
    return IntegrityError("insert", params=None, orig=Exception("conflict"))


def _create_payload(**overrides) -> UserCreate:
    return UserCreate(
        email="alice@example.com",
        full_name="Alice",
        is_active=True,
        password="hunter2hunter2",
        **overrides,
    )


def test_role_service_uses_expected_entity_name():
    assert RoleService(MagicMock()).entity_name == "Role"


def test_user_role_service_uses_expected_entity_name():
    assert UserRoleService(MagicMock()).entity_name == "User role"


def test_user_service_uses_expected_entity_name(service):
    assert service.entity_name == "User"


def test_create_hashes_password_and_strips_plaintext(repository, service):
    repository.create.return_value = "user"

    result = service.create(_create_payload())

    assert result == "user"

    args, _ = repository.create.call_args
    stored = args[0]
    assert "password" not in stored
    assert stored["password_hash"].startswith("pbkdf2_sha256$")
    assert stored["email"] == "alice@example.com"
    repository.commit.assert_called_once()


def test_create_translates_integrity_error_to_409(repository, service):
    repository.create.side_effect = _integrity_error()

    with pytest.raises(HTTPException) as exc:
        service.create(_create_payload())

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    repository.rollback.assert_called_once()


def test_update_without_password_does_not_set_hash(repository, service):
    repository.get.return_value = "user"
    repository.update.return_value = "updated"

    service.update(1, UserUpdate(full_name="Alice B."))

    args, _ = repository.update.call_args
    _, data = args
    assert data == {"full_name": "Alice B."}


def test_update_with_password_hashes_and_replaces(repository, service):
    repository.get.return_value = "user"
    repository.update.return_value = "updated"

    payload = MagicMock()
    payload.model_dump.return_value = {"password": "new-password-1234"}

    service.update(1, payload)

    args, _ = repository.update.call_args
    _, data = args
    assert "password" not in data
    assert data["password_hash"].startswith("pbkdf2_sha256$")


def test_update_with_empty_payload_returns_existing_user(repository, service):
    repository.get.return_value = "user"

    result = service.update(1, UserUpdate())

    assert result == "user"
    repository.update.assert_not_called()


def test_update_translates_integrity_error_to_409(repository, service):
    repository.get.return_value = "user"
    repository.update.side_effect = _integrity_error()

    with pytest.raises(HTTPException) as exc:
        service.update(1, UserUpdate(full_name="Alice B."))

    assert exc.value.status_code == status.HTTP_409_CONFLICT
    repository.rollback.assert_called_once()
