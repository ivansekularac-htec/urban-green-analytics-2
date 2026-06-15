from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_status import SensorStatus


def test_sensor_model_creation1():
    sensor = Sensor(
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
        installed_at=None,
        created_at=1000,
        updated_at=1000,
    )

    assert sensor.serial_number == "SN-001"
    assert sensor.status == SensorStatus.ACTIVE


def test_sensor_model_creation2():
    sensor = Sensor(
        farm_id=2,
        sensor_type_id=2,
        serial_number="SN-002",
        status=SensorStatus.ACTIVE,
        installed_at=None,
    )

    assert sensor.serial_number == "SN-002"
    assert sensor.status == SensorStatus.ACTIVE
