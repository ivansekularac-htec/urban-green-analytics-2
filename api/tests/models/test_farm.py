from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus


def test_farm_model_creation():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=2,
        name="Test Farm",
        city="Belgrade",
        size_m2=100.5,
        growing_beds_count=10,
        status=FarmStatus.ACTIVE,
    )

    assert farm.name == "Test Farm"
    assert farm.status == FarmStatus.ACTIVE
    assert farm.growing_beds_count == 10
