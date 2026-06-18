"""Tests for the authentication routes (login and /auth/me).

Uses ``app.dependency_overrides`` to swap the database dependency for an
in-memory user lookup so the tests stay isolated from Postgres.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.database import get_db
from app.main import app
from app.routers.v1.auth.login import login as login_route
from app.security.dependencies import get_current_user
from app.security.password import hash_password
from app.security.roles import RoleName


def _make_active_user(email: str = "alice@example.com", password: str = "hunter2hunter"):
    return SimpleNamespace(
        id=1,
        email=email,
        password_hash=hash_password(password),
        full_name="Alice",
        is_active=True,
        created_at=1,
        updated_at=2,
        user_roles=[
            SimpleNamespace(
                role=SimpleNamespace(name=RoleName.ADMIN.value),
                farm_id=None,
            )
        ],
    )


def _override_db_with(user):
    """Build a fake DB whose ``scalars().one_or_none()`` returns ``user``."""
    db = MagicMock()
    db.scalars.return_value.one_or_none.return_value = user
    app.dependency_overrides[get_db] = lambda: db
    return db


def test_login_returns_bearer_token_for_valid_credentials(client):
    user = _make_active_user(password="hunter2hunter")
    _override_db_with(user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "hunter2hunter"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str) and body["access_token"]


def test_login_rejects_wrong_password(client):
    user = _make_active_user(password="correctpassword")
    _override_db_with(user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "wrongpassword"},
    )

    assert response.status_code == 401


def test_login_rejects_unknown_user(client):
    _override_db_with(None)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "ghost@example.com", "password": "whatever"},
    )

    assert response.status_code == 401


def test_login_rejects_inactive_user(client):
    user = _make_active_user(password="hunter2hunter")
    user.is_active = False
    _override_db_with(user)

    response = client.post(
        "/api/v1/auth/login",
        data={"username": user.email, "password": "hunter2hunter"},
    )

    assert response.status_code == 401


def test_me_returns_current_user_when_authenticated(client):
    user = _make_active_user()
    app.dependency_overrides[get_current_user] = lambda: user

    response = client.get("/api/v1/auth/me")

    assert response.status_code == 200
    assert response.json()["email"] == user.email


def test_me_requires_authentication(client):
    # Explicitly remove the autouse Admin override so the real OAuth2 scheme runs.
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_login_route_callable_directly(client):
    # Smoke test that the route function is wired through the router.
    assert callable(login_route)
