from decimal import Decimal

from app.models.harvests.harvest import Harvest
from app.schemas.harvests.harvest import HarvestResponse


def test_harvest_model_to_schema():
    harvest = Harvest(
        id=1,
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("125.500"),
        created_at=1710000000,
        updated_at=1710000000,
    )

    response = HarvestResponse.model_validate(harvest)

    assert response.id == 1
    assert response.farm_id == 1
    assert response.crop_id == 2
    assert response.quality_grade_id == 3
    assert float(response.weight_kg) == 125.5
