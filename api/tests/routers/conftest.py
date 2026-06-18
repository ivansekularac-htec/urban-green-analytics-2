"""Shared fixtures and a CRUD helper for router tests.

Router tests use FastAPI's :class:`TestClient` against the real ``app``,
overriding the per-route service dependency with a ``MagicMock`` so no
database, repository, or service code is exercised. Service-layer
behaviour is covered separately in ``tests/services``.
"""

from collections.abc import Callable
from dataclasses import dataclass
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.dependencies.auth import get_current_user
from app.main import app


@dataclass
class RouteCase:
    """Minimal description of an entity's CRUD endpoint surface."""

    name: str
    path: str
    dependency: Callable
    create_payload: dict
    update_payload: dict


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def service() -> MagicMock:
    return MagicMock()


@pytest.fixture(autouse=True)
def _reset_dependency_overrides():
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def admin_user():
    user = MagicMock()
    user.is_active = True

    admin_role = MagicMock()
    admin_role.name = "Admin"

    user_role = MagicMock()
    user_role.role = admin_role
    user_role.farm_id = None

    user.user_roles = [user_role]

    return user


@pytest.fixture(autouse=True)
def override_auth(admin_user):
    app.dependency_overrides[get_current_user] = lambda: admin_user

    yield

    app.dependency_overrides.pop(get_current_user, None)


def assert_crud_endpoints(client: TestClient, service: MagicMock, case: RouteCase):
    """Exercise the five standard CRUD endpoints for one entity.

    The mock service is configured to return a representative payload; we
    only verify status codes and that the router delegated correctly. The
    response model is FastAPI's responsibility and is validated implicitly
    by a successful 2xx status.
    """

    app.dependency_overrides[case.dependency] = lambda: service

    representative = {**case.create_payload, "id": 1, "created_at": 1, "updated_at": 2}
    service.list.return_value = [representative]
    service.get.return_value = representative
    service.create.return_value = representative
    service.update.return_value = representative

    list_response = client.get(case.path, params={"skip": 5, "limit": 25})
    assert list_response.status_code == 200
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
