"""Tests for the sensor and sensor-type routers."""

from unittest.mock import MagicMock

import pytest

from app.routers.v1.sensors.sensor import get_sensor_service
from app.routers.v1.sensors.sensor_type import get_sensor_type_service
from app.services.sensors.sensor import SensorService
from app.services.sensors.sensor_type import SensorTypeService
from tests.routers.conftest import RouteCase, assert_crud_endpoints

CASES = [
    RouteCase(
        name="sensors",
        path="/api/v1/sensors",
        dependency=get_sensor_service,
        create_payload={
            "farm_id": 1,
            "sensor_type_id": 1,
            "serial_number": "SN-1",
            "status": "ACTIVE",
            "installed_at": 1,
        },
        update_payload={"status": "OFFLINE"},
        scoped=True,
    ),
    RouteCase(
        name="sensor-types",
        path="/api/v1/sensor-types",
        dependency=get_sensor_type_service,
        create_payload={
            "name": "Temp",
            "unit": "C",
            "description": "Temperature",
            "optimal_min": 10,
            "optimal_max": 30,
        },
        update_payload={"description": "Updated"},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_crud_endpoints(client, service, case):
    assert_crud_endpoints(client, service, case)


def test_get_sensor_service_factory_constructs_service():
    assert isinstance(get_sensor_service(MagicMock()), SensorService)


def test_get_sensor_type_service_factory_constructs_service():
    assert isinstance(get_sensor_type_service(MagicMock()), SensorTypeService)
