"""Authorization matrix — verifies which roles can access which endpoints.

Uses dependency overrides to swap ``get_current_user`` for stub users
with the desired role mix (or no override at all to simulate an
unauthenticated request). The service layer is mocked so this test
exercises only the router-level role gate.

The ``_admin_auth_override`` autouse fixture from
``tests/routers/conftest.py`` runs first; each test below either
re-overrides ``get_current_user`` or pops the override entirely.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from app.main import app
from app.routers.v1.crops.crop import get_crop_service
from app.routers.v1.crops.farm_crop import get_farm_crop_service
from app.routers.v1.farms.farm import get_farm_service
from app.routers.v1.harvests.harvest import get_harvest_service
from app.routers.v1.sensors.sensor import get_sensor_service
from app.routers.v1.users.user import get_user_service
from app.security.dependencies import get_current_user
from app.security.roles import RoleName

# ---------------------------------------------------------------------
# Stub users for each role combination
# ---------------------------------------------------------------------


def _user(roles):
    return SimpleNamespace(
        id=1,
        email="u@example.com",
        full_name="User",
        is_active=True,
        user_roles=[
            SimpleNamespace(role=SimpleNamespace(name=role.value), farm_id=farm_id)
            for role, farm_id in roles
        ],
    )


ADMIN = _user([(RoleName.ADMIN, None)])
FARM_MANAGER_FARM_1 = _user([(RoleName.FARM_MANAGER, 1)])
OPS_FARM_1 = _user([(RoleName.OPERATIONS_TEAM, 1)])


def _as_user(user):
    """Override ``get_current_user`` to yield ``user`` for the next request."""
    app.dependency_overrides[get_current_user] = lambda: user


def _as_anonymous():
    """Drop the auth override so the real OAuth2 scheme runs and rejects."""
    app.dependency_overrides.pop(get_current_user, None)


# ---------------------------------------------------------------------
# Mock service helpers
# ---------------------------------------------------------------------


def _mock_service_for(dependency, *, scoped_id_returns_farm: int | None = None):
    """Install a MagicMock service with sensible CRUD return values.

    ``scoped_id_returns_farm`` lets callers pin the ``farm_id`` of items
    returned by ``service.get`` so post-fetch ``assert_farm_in_scope``
    checks see a known farm.
    """
    service = MagicMock()
    item = SimpleNamespace(
        id=1,
        farm_id=scoped_id_returns_farm or 1,
        crop_id=1,
        quality_grade_id=1,
        weight_kg=5,
        sensor_type_id=1,
        serial_number="SN",
        status="ACTIVE",
        installed_at=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="x",
        city="x",
        size_m2=1,
        growing_beds_count=1,
        started_at=1,
        ended_at=2,
        category_id=1,
        description="x",
        email="x@example.com",
        full_name="x",
        is_active=True,
        password_hash="x",
        created_at=1,
        updated_at=1,
    )
    service.list.return_value = [item]
    service.get.return_value = item
    service.create.return_value = item
    service.update.return_value = item
    app.dependency_overrides[dependency] = lambda: service
    return service


# ---------------------------------------------------------------------
# Anonymous → 401 across the board
# ---------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/sensors",
        "/api/v1/harvests",
        "/api/v1/farms",
        "/api/v1/farm-crops",
        "/api/v1/users",
        "/api/v1/crops",
        "/api/v1/auth/me",
    ],
)
def test_anonymous_request_is_rejected(client, path):
    _as_anonymous()
    response = client.get(path)
    assert response.status_code == 401


# ---------------------------------------------------------------------
# Admin can do everything
# ---------------------------------------------------------------------


def test_admin_can_list_sensors(client):
    _as_user(ADMIN)
    _mock_service_for(get_sensor_service)
    assert client.get("/api/v1/sensors").status_code == 200


def test_admin_can_create_sensor(client):
    _as_user(ADMIN)
    _mock_service_for(get_sensor_service)
    payload = {
        "farm_id": 1,
        "sensor_type_id": 1,
        "serial_number": "SN-1",
        "status": "ACTIVE",
        "installed_at": 1,
    }
    assert client.post("/api/v1/sensors", json=payload).status_code == 201


def test_admin_can_list_users(client):
    _as_user(ADMIN)
    _mock_service_for(get_user_service)
    assert client.get("/api/v1/users").status_code == 200


# ---------------------------------------------------------------------
# Farm Manager — read scoped, no writes
# ---------------------------------------------------------------------


def test_farm_manager_can_list_sensors(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_sensor_service)
    response = client.get("/api/v1/sensors")
    assert response.status_code == 200


def test_farm_manager_cannot_create_sensor(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_sensor_service)
    payload = {
        "farm_id": 1,
        "sensor_type_id": 1,
        "serial_number": "SN-1",
        "status": "ACTIVE",
        "installed_at": 1,
    }
    assert client.post("/api/v1/sensors", json=payload).status_code == 403


def test_farm_manager_cannot_list_users(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_user_service)
    assert client.get("/api/v1/users").status_code == 403


def test_farm_manager_cannot_create_harvest(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_harvest_service)
    payload = {"farm_id": 1, "crop_id": 1, "quality_grade_id": 1, "weight_kg": 5}
    assert client.post("/api/v1/harvests", json=payload).status_code == 403


def test_farm_manager_cannot_see_other_farms_sensor_detail(client):
    _as_user(FARM_MANAGER_FARM_1)
    # Service returns a sensor on farm 99, FM only manages farm 1 → 404 (hidden).
    _mock_service_for(get_sensor_service, scoped_id_returns_farm=99)
    assert client.get("/api/v1/sensors/1").status_code == 404


def test_farm_manager_can_see_own_farms_sensor_detail(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_sensor_service, scoped_id_returns_farm=1)
    assert client.get("/api/v1/sensors/1").status_code == 200


# ---------------------------------------------------------------------
# Operations Team — read scoped, write harvests scoped
# ---------------------------------------------------------------------


def test_ops_can_list_sensors(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_sensor_service)
    assert client.get("/api/v1/sensors").status_code == 200


def test_ops_cannot_create_sensor(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_sensor_service)
    payload = {
        "farm_id": 1,
        "sensor_type_id": 1,
        "serial_number": "SN-1",
        "status": "ACTIVE",
        "installed_at": 1,
    }
    assert client.post("/api/v1/sensors", json=payload).status_code == 403


def test_ops_can_create_harvest_on_own_farm(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_harvest_service)
    payload = {"farm_id": 1, "crop_id": 1, "quality_grade_id": 1, "weight_kg": 5}
    assert client.post("/api/v1/harvests", json=payload).status_code == 201


def test_ops_cannot_create_harvest_on_other_farm(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_harvest_service)
    payload = {"farm_id": 99, "crop_id": 1, "quality_grade_id": 1, "weight_kg": 5}
    assert client.post("/api/v1/harvests", json=payload).status_code == 403


def test_ops_can_update_harvest_on_own_farm(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_harvest_service, scoped_id_returns_farm=1)
    response = client.put("/api/v1/harvests/1", json={"weight_kg": 6})
    assert response.status_code == 200


def test_ops_cannot_update_harvest_on_other_farm(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_harvest_service, scoped_id_returns_farm=99)
    response = client.put("/api/v1/harvests/1", json={"weight_kg": 6})
    assert response.status_code == 403


# ---------------------------------------------------------------------
# Reference data — any authenticated user can read; only Admin writes
# ---------------------------------------------------------------------


def test_farm_manager_can_read_reference_data(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_crop_service)
    assert client.get("/api/v1/crops").status_code == 200


def test_ops_cannot_create_crop(client):
    _as_user(OPS_FARM_1)
    _mock_service_for(get_crop_service)
    payload = {"name": "Basil", "description": "Herb", "category_id": 1}
    assert client.post("/api/v1/crops", json=payload).status_code == 403


# ---------------------------------------------------------------------
# Farm-crops scoping
# ---------------------------------------------------------------------


def test_farm_manager_can_list_farm_crops(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_farm_crop_service)
    assert client.get("/api/v1/farm-crops").status_code == 200


def test_farm_manager_cannot_create_farm(client):
    _as_user(FARM_MANAGER_FARM_1)
    _mock_service_for(get_farm_service)
    payload = {
        "infrastructure_type_id": 1,
        "growing_system_type_id": 1,
        "name": "Farm",
        "city": "Belgrade",
        "size_m2": 100,
        "status": "ACTIVE",
        "growing_beds_count": 4,
    }
    assert client.post("/api/v1/farms", json=payload).status_code == 403
