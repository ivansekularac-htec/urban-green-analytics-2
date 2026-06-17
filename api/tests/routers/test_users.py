"""Tests for the user, role, and user-role routers.

Pagination defaults and validation are also covered here, since they are
shared across every CRUD router.
"""

from unittest.mock import MagicMock

import pytest

from app.main import app
from app.routers.v1.users.role import get_role_service
from app.routers.v1.users.user import get_user_service
from app.routers.v1.users.user_role import get_user_role_service
from app.services.users.role import RoleService
from app.services.users.user import UserService
from app.services.users.user_role import UserRoleService
from tests.routers.conftest import RouteCase, assert_crud_endpoints

CASES = [
    RouteCase(
        name="users",
        path="/api/v1/users",
        dependency=get_user_service,
        create_payload={
            "email": "alice@example.com",
            "full_name": "Alice",
            "is_active": True,
            "password": "supersecret",
        },
        update_payload={"full_name": "Alice B."},
    ),
    RouteCase(
        name="roles",
        path="/api/v1/roles",
        dependency=get_role_service,
        create_payload={"name": "Admin", "description": "Administrator"},
        update_payload={"description": "Updated"},
    ),
    RouteCase(
        name="user-roles",
        path="/api/v1/user-roles",
        dependency=get_user_role_service,
        create_payload={"user_id": 1, "role_id": 1, "farm_id": 1},
        update_payload={"role_id": 2},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_crud_endpoints(client, service, case):
    assert_crud_endpoints(client, service, case)


def test_get_user_service_factory_constructs_service():
    assert isinstance(get_user_service(MagicMock()), UserService)


def test_get_role_service_factory_constructs_service():
    assert isinstance(get_role_service(MagicMock()), RoleService)


def test_get_user_role_service_factory_constructs_service():
    assert isinstance(get_user_role_service(MagicMock()), UserRoleService)


def test_pagination_uses_defaults_when_query_omitted(client, service):
    app.dependency_overrides[get_user_service] = lambda: service
    service.list.return_value = []

    response = client.get("/api/v1/users")

    assert response.status_code == 200
    service.list.assert_called_once_with(skip=0, limit=100)


def test_pagination_rejects_out_of_range_query(client, service):
    app.dependency_overrides[get_user_service] = lambda: service

    response = client.get("/api/v1/users", params={"limit": 9999})

    assert response.status_code == 422
