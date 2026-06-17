"""Tests for sensor-related repositories."""

from unittest.mock import MagicMock

from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_type import SensorType
from app.repositories.sensors.sensor import SensorRepository
from app.repositories.sensors.sensor_type import SensorTypeRepository


def test_sensor_repository_binds_sensor_model():
    assert SensorRepository(MagicMock()).model is Sensor


def test_sensor_type_repository_binds_sensor_type_model():
    assert SensorTypeRepository(MagicMock()).model is SensorType
