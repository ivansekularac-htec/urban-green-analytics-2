"""Tests for harvest-related repositories."""

from unittest.mock import MagicMock

from app.models.harvests.harvest import Harvest
from app.models.harvests.quality_grade import QualityGrade
from app.repositories.harvests.harvest import HarvestRepository
from app.repositories.harvests.quality_grade import QualityGradeRepository


def test_harvest_repository_binds_harvest_model():
    assert HarvestRepository(MagicMock()).model is Harvest


def test_quality_grade_repository_binds_quality_grade_model():
    assert QualityGradeRepository(MagicMock()).model is QualityGrade
