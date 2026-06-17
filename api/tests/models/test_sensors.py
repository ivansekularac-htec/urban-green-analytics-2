"""Tests for the sensor ORM models."""

from decimal import Decimal

from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus
from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_status import SensorStatus
from app.models.sensors.sensor_type import SensorType


def test_sensor_assigns_fields():
    sensor = Sensor(
        id=1,
        farm_id=1,
        sensor_type_id=2,
        serial_number="SN-1",
        status=SensorStatus.ACTIVE,
        installed_at=1000,
    )

    assert sensor.farm_id == 1
    assert sensor.sensor_type_id == 2
    assert sensor.serial_number == "SN-1"
    assert sensor.status == SensorStatus.ACTIVE
    assert sensor.installed_at == 1000


def test_sensor_status_enum_values():
    assert SensorStatus.ACTIVE.value == "ACTIVE"
    assert SensorStatus.OFFLINE.value == "OFFLINE"
    assert SensorStatus.MAINTENANCE.value == "MAINTENANCE"


def test_sensor_type_assigns_fields():
    sensor_type = SensorType(
        id=1,
        name="Temp",
        unit="C",
        description="Temperature",
        optimal_min=Decimal("10"),
        optimal_max=Decimal("30"),
    )

    assert sensor_type.unit == "C"
    assert sensor_type.optimal_min == Decimal("10")
    assert sensor_type.optimal_max == Decimal("30")


def test_sensor_links_to_farm_bidirectionally():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )
    sensor = Sensor(
        id=1,
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-1",
        status=SensorStatus.ACTIVE,
    )

    sensor.farm = farm

    assert sensor.farm is farm
    assert list(farm.sensors) == [sensor]
