"""Tests for farm-related services."""

from unittest.mock import MagicMock

from app.services.farms.farm import FarmService
from app.services.farms.growing_system_type import GrowingSystemTypeService
from app.services.farms.infrastructure_type import InfrastructureTypeService


def test_farm_service_uses_expected_entity_name():
    assert FarmService(MagicMock()).entity_name == "Farm"


def test_growing_system_type_service_uses_expected_entity_name():
    assert GrowingSystemTypeService(MagicMock()).entity_name == "Growing system type"


def test_infrastructure_type_service_uses_expected_entity_name():
    assert InfrastructureTypeService(MagicMock()).entity_name == "Infrastructure type"
