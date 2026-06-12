"""
Tests for Pydantic schema validation and ORM object serialization.
"""

from decimal import Decimal

from app.models.harvest import Harvest
from app.models.quality_grade import QualityGrade
from app.schemas.harvest import HarvestCreate, HarvestResponse
from app.schemas.quality_grade import QualityGradeCreate, QualityGradeResponse


def test_quality_grade_create_schema_validation() -> None:
    """Verify that QualityGradeCreate validates valid input data."""

    schema = QualityGradeCreate(
        code="A",
        name="Premium",
        description="Highest quality harvest grade.",
    )

    assert schema.code == "A"
    assert schema.name == "Premium"
    assert schema.description == "Highest quality harvest grade."


def test_quality_grade_response_schema_from_orm_model() -> None:
    """Verify that QualityGradeResponse can serialize an ORM model instance."""

    quality_grade = QualityGrade(
        id=1,
        code="A",
        name="Premium",
        description="Highest quality harvest grade.",
        created_at=1_718_200_000,
        updated_at=1_718_200_000,
    )

    schema = QualityGradeResponse.model_validate(quality_grade)

    assert schema.id == 1
    assert schema.code == "A"
    assert schema.name == "Premium"
    assert schema.description == "Highest quality harvest grade."
    assert schema.created_at == 1_718_200_000
    assert schema.updated_at == 1_718_200_000


def test_harvest_create_schema_validation() -> None:
    """Verify that HarvestCreate validates valid input data."""

    schema = HarvestCreate(
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("12.500"),
    )

    assert schema.farm_id == 1
    assert schema.crop_id == 2
    assert schema.quality_grade_id == 3
    assert schema.weight_kg == Decimal("12.500")


def test_harvest_response_schema_from_orm_model() -> None:
    """Verify that HarvestResponse can serialize an ORM model instance."""

    harvest = Harvest(
        id=1,
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("12.500"),
        created_at=1_718_200_000,
        updated_at=1_718_200_000,
    )

    schema = HarvestResponse.model_validate(harvest)

    assert schema.id == 1
    assert schema.farm_id == 1
    assert schema.crop_id == 2
    assert schema.quality_grade_id == 3
    assert schema.weight_kg == Decimal("12.500")
    assert schema.created_at == 1_718_200_000
    assert schema.updated_at == 1_718_200_000
