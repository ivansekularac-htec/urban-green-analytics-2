from app.schemas.farms.farm import FarmBase, FarmCreate, FarmResponse, FarmUpdate


def test_farm_base_schema():
    data = {
        "infrastructure_type_id": 1,
        "growing_system_type_id": 2,
        "name": "Test Farm",
        "city": "Belgrade",
        "size_m2": 100.5,
        "growing_beds_count": 10,
    }

    farm = FarmBase(**data)

    assert farm.name == "Test Farm"
    assert farm.city == "Belgrade"


def test_farm_create_schema():
    data = {
        "infrastructure_type_id": 1,
        "growing_system_type_id": 2,
        "name": "Create Farm",
    }

    farm = FarmCreate(**data)

    assert farm.name == "Create Farm"


def test_farm_update_schema_partial():
    data = {
        "name": "Updated Farm",
    }

    farm = FarmUpdate(**data)

    assert farm.name == "Updated Farm"
    assert farm.city is None


def test_farm_response_schema():
    data = {
        "id": 1,
        "status": "ACTIVE",
        "infrastructure_type_id": 1,
        "growing_system_type_id": 2,
        "name": "Response Farm",
        "city": "Belgrade",
        "size_m2": 50.0,
        "growing_beds_count": 5,
        "created_at": 1710000000,
        "updated_at": 1710000500,
    }

    farm = FarmResponse(**data)

    assert farm.id == 1
    assert farm.status == "ACTIVE"
