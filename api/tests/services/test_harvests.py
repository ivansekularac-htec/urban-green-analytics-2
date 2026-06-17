"""Tests for harvest-related services."""

from unittest.mock import MagicMock

from app.services.harvests.harvest import HarvestService
from app.services.harvests.quality_grade import QualityGradeService


def test_harvest_service_uses_expected_entity_name():
    assert HarvestService(MagicMock()).entity_name == "Harvest"


def test_quality_grade_service_uses_expected_entity_name():
    assert QualityGradeService(MagicMock()).entity_name == "Quality grade"
