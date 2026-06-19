"""Shared fixtures and a CRUD helper for router tests.

Router tests use FastAPI's :class:`TestClient` against the real ``app``,
overriding the per-route service dependency with a ``MagicMock`` so no
database, repository, or service code is exercised. Service-layer
behaviour is covered separately in ``tests/services``.

Auth is overridden globally via :func:`get_current_user` to return an
in-memory Admin user so existing CRUD tests don't need to manage tokens.
Authorization-specific behaviour is covered separately in
``tests/routers/test_authorization.py``.
"""

from collections.abc import Callable
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.security.dependencies import get_current_user
from app.security.roles import RoleName


def make_user(
    roles: list[tuple[RoleName, int | None]], *, is_active: bool = True, user_id: int = 1
):
    """Build a stub :class:`User` for dependency overrides.

    ``roles`` is a list of ``(role_name, farm_id)`` pairs — ``farm_id``
    may be ``None`` for system-wide roles like Admin.
    """
    user_roles = [
        SimpleNamespace(role=SimpleNamespace(name=role.value), farm_id=farm_id)
        for role, farm_id in roles
    ]
    return SimpleNamespace(
        id=user_id,
        email="user@example.com",
        full_name="Test User",
        is_active=is_active,
        user_roles=user_roles,
    )


ADMIN_USER = make_user([(RoleName.ADMIN, None)])


@dataclass
class RouteCase:
    """Minimal description of an entity's CRUD endpoint surface."""

    name: str
    path: str
    dependency: Callable
    create_payload: dict
    update_payload: dict
    scoped: bool = False
    """When True, the list endpoint takes a farm-scope filter
    (``farm_ids=None`` for Admin) and the assertions account for that."""


@pytest.fixture
def client() -> TestClient:
    # Patch the startup hooks so :class:`TestClient` doesn't try to talk
    # to a real Postgres or run ``ensure_superuser`` against it.
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
    ):
        yield TestClient(app)


@pytest.fixture
def service() -> MagicMock:
    return MagicMock()


@pytest.fixture(autouse=True)
def _admin_auth_override():
    """Authenticate every router test as Admin by default.

    Individual tests can override this by writing a different value to
    ``app.dependency_overrides[get_current_user]`` before issuing a
    request — :func:`_reset_dependency_overrides` cleans up after.
    """
    app.dependency_overrides[get_current_user] = lambda: ADMIN_USER
    yield


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()


def assert_crud_endpoints(client: TestClient, service: MagicMock, case: RouteCase):
    """Exercise the five standard CRUD endpoints for one entity.

    The mock service is configured to return a representative payload; we
    only verify status codes and that the router delegated correctly. The
    response model is FastAPI's responsibility and is validated implicitly
    by a successful 2xx status.
    """

    app.dependency_overrides[case.dependency] = lambda: service

    representative_dict = {**case.create_payload, "id": 1, "created_at": 1, "updated_at": 2}
    # SimpleNamespace supports attribute access (needed by routers that
    # post-fetch the row to enforce farm scoping) while still being
    # serializable by ``from_attributes=True`` response models.
    representative_obj = SimpleNamespace(**representative_dict)
    service.list.return_value = [representative_obj]
    service.get.return_value = representative_obj
    service.create.return_value = representative_obj
    service.update.return_value = representative_obj

    list_response = client.get(case.path, params={"skip": 5, "limit": 25})
    assert list_response.status_code == 200
    if case.scoped:
        service.list.assert_called_once_with(skip=5, limit=25, farm_ids=None)
    else:
        service.list.assert_called_once_with(skip=5, limit=25)

    get_response = client.get(f"{case.path}/1")
    assert get_response.status_code == 200
    service.get.assert_called_once_with(1)

    create_response = client.post(case.path, json=case.create_payload)
    assert create_response.status_code == 201
    service.create.assert_called_once()

    update_response = client.put(f"{case.path}/1", json=case.update_payload)
    assert update_response.status_code == 200
    update_args, _ = service.update.call_args
    assert update_args[0] == 1

    delete_response = client.delete(f"{case.path}/1")
    assert delete_response.status_code == 204
    service.delete.assert_called_once_with(1)
