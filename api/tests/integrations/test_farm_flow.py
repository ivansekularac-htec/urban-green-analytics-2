from app.models.farms.farm import Farm
from app.schemas.farms.farm import FarmResponse
from app.models.farms.farm_status import FarmStatus

from app.models.sensors.sensor import Sensor
from app.models.sensors.sensor_status import SensorStatus

def test_farm_flow():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        city="Belgrade",
        size_m2=150.5,
        status=FarmStatus.ACTIVE,
        created_at=1000,
        updated_at=1000,
    )

    schema = FarmResponse.model_validate(farm)

    assert schema.name == "Farm"
    assert schema.status == FarmStatus.ACTIVE


def test_farm_sensor_relationship():
    farm = Farm(
        id=2,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm A",
        city="Belgrade",
        status=FarmStatus.ACTIVE,
        created_at=1000,
        updated_at=1000,
    )

    sensor = Sensor(
        id=1,
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
        created_at=1000,
        updated_at=1000,
    )

    sensor.farm = farm

    assert sensor.farm == farm


def test_farm_sensor_bidirectional_relationship():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm A",
        status=FarmStatus.ACTIVE,
        created_at=1000,
        updated_at=1000,
    )

    sensor = Sensor(
        id=1,
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
        created_at=1000,
        updated_at=1000,
    )

    farm.sensors.append(sensor)

    assert len(farm.sensors) == 1
    assert farm.sensors[0] == sensor