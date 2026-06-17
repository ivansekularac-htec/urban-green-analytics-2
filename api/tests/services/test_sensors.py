"""Tests for sensor-related services."""

from unittest.mock import MagicMock

from app.services.sensors.sensor import SensorService
from app.services.sensors.sensor_type import SensorTypeService


def test_sensor_service_uses_expected_entity_name():
    assert SensorService(MagicMock()).entity_name == "Sensor"


def test_sensor_type_service_uses_expected_entity_name():
    assert SensorTypeService(MagicMock()).entity_name == "Sensor type"
