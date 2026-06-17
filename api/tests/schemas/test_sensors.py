"""Tests for sensor and sensor-type schemas."""

from decimal import Decimal

from app.models.sensors.sensor_status import SensorStatus
from app.schemas.sensors.sensor import SensorCreate, SensorResponse, SensorUpdate
from app.schemas.sensors.sensor_type import (
    SensorTypeCreate,
    SensorTypeResponse,
    SensorTypeUpdate,
)


def test_sensor_create_accepts_valid_payload():
    create = SensorCreate(
        farm_id=1,
        sensor_type_id=2,
        serial_number="SN-1",
        status=SensorStatus.ACTIVE,
        installed_at=10,
    )

    assert create.serial_number == "SN-1"
    assert create.status is SensorStatus.ACTIVE


def test_sensor_update_accepts_partial_payload():
    update = SensorUpdate(serial_number="SN-2", status=SensorStatus.OFFLINE)

    assert update.serial_number == "SN-2"
    assert update.status is SensorStatus.OFFLINE


def test_sensor_response_round_trip():
    response = SensorResponse(
        id=1,
        farm_id=1,
        sensor_type_id=2,
        serial_number="SN-1",
        status=SensorStatus.ACTIVE,
        installed_at=10,
        created_at=1,
        updated_at=2,
    )

    assert response.id == 1


def test_sensor_type_create_update_response():
    create = SensorTypeCreate(
        name="Temp",
        unit="C",
        description="Temperature",
        optimal_min=Decimal("10"),
        optimal_max=Decimal("30"),
    )
    update = SensorTypeUpdate(description="Updated")
    response = SensorTypeResponse(
        id=1,
        name="Temp",
        unit="C",
        description="Temperature",
        optimal_min=Decimal("10"),
        optimal_max=Decimal("30"),
        created_at=1,
        updated_at=2,
    )

    assert create.unit == "C"
    assert update.description == "Updated"
    assert response.optimal_min == Decimal("10")
