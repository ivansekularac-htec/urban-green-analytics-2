"""Tests for farm, infrastructure-type, and growing-system-type schemas."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus
from app.schemas.farms.farm import FarmCreate, FarmResponse, FarmUpdate
from app.schemas.farms.growing_system_type import (
    GrowingSystemTypeCreate,
    GrowingSystemTypeResponse,
    GrowingSystemTypeUpdate,
)
from app.schemas.farms.infrastructure_type import (
    InfrastructureTypeCreate,
    InfrastructureTypeResponse,
    InfrastructureTypeUpdate,
)


def test_farm_create_accepts_valid_payload():
    create = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        city="Belgrade",
        size_m2=Decimal("12.5"),
        status=FarmStatus.ACTIVE,
        growing_beds_count=4,
    )

    assert create.name == "Farm"
    assert create.status is FarmStatus.ACTIVE


def test_farm_create_rejects_non_positive_size():
    with pytest.raises(ValidationError):
        FarmCreate(
            infrastructure_type_id=1,
            growing_system_type_id=1,
            name="Farm",
            size_m2=Decimal("-1"),
        )


def test_farm_update_accepts_partial_payload():
    update = FarmUpdate(name="Renamed", status=FarmStatus.INACTIVE)

    assert update.name == "Renamed"
    assert update.status is FarmStatus.INACTIVE


def test_farm_response_supports_from_attributes():
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        city="Belgrade",
        size_m2=Decimal("12.5"),
        status=FarmStatus.ACTIVE,
        growing_beds_count=4,
        created_at=1,
        updated_at=2,
    )

    response = FarmResponse.model_validate(farm)

    assert response.id == 1
    assert response.status is FarmStatus.ACTIVE


def test_growing_system_type_create_update_response():
    create = GrowingSystemTypeCreate(name="Vertical", description="Tower")
    update = GrowingSystemTypeUpdate(description="Updated")
    response = GrowingSystemTypeResponse(
        id=1,
        name="Vertical",
        description="Tower",
        created_at=1,
        updated_at=2,
    )

    assert create.name == "Vertical"
    assert update.description == "Updated"
    assert response.id == 1


def test_infrastructure_type_create_update_response():
    create = InfrastructureTypeCreate(name="Hydro", description="Soilless")
    update = InfrastructureTypeUpdate(description="Updated")
    response = InfrastructureTypeResponse(
        id=1,
        name="Hydro",
        description="Soilless",
        created_at=1,
        updated_at=2,
    )

    assert create.name == "Hydro"
    assert update.description == "Updated"
    assert response.id == 1
