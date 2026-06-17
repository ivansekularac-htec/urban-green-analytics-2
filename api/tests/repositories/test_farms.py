"""Tests for farm-related repositories."""

from unittest.mock import MagicMock

from app.models.farms.farm import Farm
from app.models.farms.growing_system_type import GrowingSystemType
from app.models.farms.infrastructure_type import InfrastructureType
from app.repositories.farms.farm import FarmRepository
from app.repositories.farms.growing_system_type import GrowingSystemTypeRepository
from app.repositories.farms.infrastructure_type import InfrastructureTypeRepository


def test_farm_repository_binds_farm_model():
    assert FarmRepository(MagicMock()).model is Farm


def test_growing_system_type_repository_binds_growing_system_type_model():
    assert GrowingSystemTypeRepository(MagicMock()).model is GrowingSystemType


def test_infrastructure_type_repository_binds_infrastructure_type_model():
    assert InfrastructureTypeRepository(MagicMock()).model is InfrastructureType
