from unittest.mock import MagicMock

from app.dependencies.auth import get_current_user
from app.main import app
from app.routers.v1.users.user import get_user_service


def make_user(role_name: str):
    user = MagicMock()
    user.is_active = True

    role = MagicMock()
    role.name = role_name

    user_role = MagicMock()
    user_role.role = role
    user_role.farm_id = None

    user.user_roles = [user_role]

    return user


def test_protected_route_without_token_returns_401(client):
    app.dependency_overrides.pop(get_current_user, None)

    response = client.get("/api/v1/users")

    assert response.status_code == 401


def test_admin_can_access_users(client):
    service = MagicMock()
    service.list.return_value = []

    app.dependency_overrides[get_current_user] = lambda: make_user("Admin")
    app.dependency_overrides[get_user_service] = lambda: service

    response = client.get("/api/v1/users")

    assert response.status_code != 401
    assert response.status_code != 403


def test_non_admin_cannot_access_users(client):
    app.dependency_overrides[get_current_user] = lambda: make_user("Operations Team")

    response = client.get("/api/v1/users")

    assert response.status_code == 403
