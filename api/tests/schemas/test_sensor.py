from app.models.sensors.sensor_status import SensorStatus
from app.schemas.sensors.sensor import SensorBase, SensorCreate, SensorResponse


def test_sensor_base():
    sensor = SensorBase(
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
        installed_at=1710000000,
    )

    assert sensor.serial_number == "SN-001"
    assert sensor.status == SensorStatus.ACTIVE


def test_sensor_create():
    sensor = SensorCreate(
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
    )

    assert sensor.farm_id == 1


def test_sensor_response():
    sensor = SensorResponse(
        id=1,
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
        installed_at=1710000000,
        created_at=1710000000,
        updated_at=1710000000,
    )

    assert sensor.id == 1
