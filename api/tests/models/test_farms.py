"""Tests for the farm ORM models."""

from decimal import Decimal

from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus
from app.models.farms.growing_system_type import GrowingSystemType
from app.models.farms.infrastructure_type import InfrastructureType


def test_farm_assigns_fields():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=2,
        name="Farm",
        city="Belgrade",
        size_m2=Decimal("100.5"),
        status=FarmStatus.ACTIVE,
        growing_beds_count=4,
    )

    assert farm.name == "Farm"
    assert farm.city == "Belgrade"
    assert farm.size_m2 == Decimal("100.5")
    assert farm.status == FarmStatus.ACTIVE
    assert farm.growing_beds_count == 4


def test_farm_status_enum_values():
    assert FarmStatus.ACTIVE.value == "ACTIVE"
    assert FarmStatus.MAINTENANCE.value == "MAINTENANCE"
    assert FarmStatus.INACTIVE.value == "INACTIVE"


def test_growing_system_type_assigns_fields():
    system = GrowingSystemType(id=1, name="Vertical", description="Tower")

    assert system.name == "Vertical"
    assert system.description == "Tower"


def test_infrastructure_type_assigns_fields():
    infra = InfrastructureType(id=1, name="Hydro", description="Soilless")

    assert infra.name == "Hydro"
    assert infra.description == "Soilless"


def test_farm_keeps_relationships_to_supporting_types():
    infra = InfrastructureType(id=1, name="Hydro")
    system = GrowingSystemType(id=1, name="Vertical")
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )

    farm.infrastructure_type = infra
    farm.growing_system_type = system

    assert farm.infrastructure_type is infra
    assert farm.growing_system_type is system
