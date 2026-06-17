from app.schemas.harvests.harvest import HarvestResponse


def test_harvest_response_schema():
    data = {
        "id": 1,
        "farm_id": 1,
        "crop_id": 2,
        "quality_grade_id": 3,
        "weight_kg": 125.5,
        "created_at": 1710000000,
        "updated_at": 1710000000,
    }

    harvest = HarvestResponse(**data)

    assert harvest.id == 1
    assert harvest.weight_kg == 125.5
