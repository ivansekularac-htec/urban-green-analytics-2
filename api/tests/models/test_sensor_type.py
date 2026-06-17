from decimal import Decimal

from app.models.sensors.sensor_type import SensorType


def test_sensor_type_creation():
    sensor_type = SensorType(
        id=1,
        name="Temperature",
        unit="°C",
        optimal_min=Decimal("10.000"),
        optimal_max=Decimal("30.000"),
        created_at=1000,
        updated_at=1000,
    )

    assert sensor_type.unit == "°C"
