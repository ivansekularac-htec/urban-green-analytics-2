"""
Tests for SQLAlchemy ORM model metadata and database schema mappings.
"""

from app.models.harvest import Harvest
from app.models.quality_grade import QualityGrade


def test_quality_grade_model_metadata() -> None:
    """Verify that the QualityGrade ORM model matches the database table metadata."""

    assert QualityGrade.__tablename__ == "quality_grades"

    columns = QualityGrade.__table__.columns

    assert "id" in columns
    assert "code" in columns
    assert "name" in columns
    assert "description" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    assert columns["id"].primary_key is True
    assert columns["code"].unique is True
    assert columns["code"].nullable is False
    assert columns["name"].nullable is False
    assert columns["description"].nullable is True
    assert columns["created_at"].nullable is False
    assert columns["updated_at"].nullable is False


def test_harvest_model_metadata() -> None:
    """Verify that the Harvest ORM model matches the database table metadata."""

    assert Harvest.__tablename__ == "harvests"

    columns = Harvest.__table__.columns

    assert "id" in columns
    assert "farm_id" in columns
    assert "crop_id" in columns
    assert "quality_grade_id" in columns
    assert "weight_kg" in columns
    assert "created_at" in columns
    assert "updated_at" in columns

    assert columns["id"].primary_key is True
    assert columns["farm_id"].nullable is False
    assert columns["crop_id"].nullable is False
    assert columns["quality_grade_id"].nullable is False
    assert columns["weight_kg"].nullable is False
    assert columns["created_at"].nullable is False
    assert columns["updated_at"].nullable is False


def test_harvest_quality_grade_foreign_key() -> None:
    """Verify that Harvest.quality_grade_id references quality_grades.id."""

    foreign_keys = Harvest.__table__.columns["quality_grade_id"].foreign_keys

    assert len(foreign_keys) == 1

    foreign_key = next(iter(foreign_keys))

    assert foreign_key.target_fullname == "quality_grades.id"
