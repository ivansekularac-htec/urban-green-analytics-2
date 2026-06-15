from decimal import Decimal

from app.models.harvests.harvest import Harvest


def test_harvest_model_creation():
    harvest = Harvest(
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("125.500"),
        created_at=1710000000,
        updated_at=1710000000,
    )

    assert harvest.farm_id == 1
    assert harvest.crop_id == 2
    assert harvest.quality_grade_id == 3
    assert harvest.weight_kg == Decimal("125.500")