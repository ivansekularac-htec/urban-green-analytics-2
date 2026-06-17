"""Tests for the harvest ORM models."""

from decimal import Decimal

from app.models.harvests.harvest import Harvest
from app.models.harvests.quality_grade import QualityGrade


def test_harvest_assigns_fields():
    harvest = Harvest(
        id=1,
        farm_id=1,
        crop_id=2,
        quality_grade_id=3,
        weight_kg=Decimal("12.500"),
    )

    assert harvest.farm_id == 1
    assert harvest.crop_id == 2
    assert harvest.quality_grade_id == 3
    assert harvest.weight_kg == Decimal("12.500")


def test_quality_grade_assigns_fields():
    grade = QualityGrade(id=1, code="A", name="Premium", description="Top")

    assert grade.code == "A"
    assert grade.name == "Premium"
    assert grade.description == "Top"


def test_harvest_links_to_quality_grade():
    grade = QualityGrade(id=1, code="A", name="Premium")
    harvest = Harvest(id=1, farm_id=1, crop_id=1, quality_grade_id=1, weight_kg=1)

    harvest.quality_grade = grade

    assert harvest.quality_grade is grade
    assert list(grade.harvests) == [harvest]
