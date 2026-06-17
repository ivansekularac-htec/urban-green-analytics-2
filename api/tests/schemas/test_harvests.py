"""Tests for harvest and quality-grade schemas."""

from decimal import Decimal

from app.schemas.harvests.harvest import HarvestCreate, HarvestResponse, HarvestUpdate
from app.schemas.harvests.quality_grade import (
    QualityGradeCreate,
    QualityGradeResponse,
    QualityGradeUpdate,
)


def test_harvest_create_accepts_valid_payload():
    create = HarvestCreate(
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("12.5"),
    )

    assert create.farm_id == 1
    assert create.weight_kg == Decimal("12.5")


def test_harvest_update_accepts_partial_payload():
    update = HarvestUpdate(weight_kg=Decimal("9"), quality_grade_id=5)

    assert update.weight_kg == Decimal("9")


def test_harvest_response_round_trip():
    response = HarvestResponse(
        id=1,
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("12.5"),
        created_at=1,
        updated_at=2,
    )

    assert response.id == 1


def test_quality_grade_create_update_response():
    create = QualityGradeCreate(code="A", name="Premium", description="Top")
    update = QualityGradeUpdate(name="Standard")
    response = QualityGradeResponse(
        id=1,
        code="A",
        name="Premium",
        description="Top",
        created_at=1,
        updated_at=2,
    )

    assert create.code == "A"
    assert update.name == "Standard"
    assert response.id == 1
