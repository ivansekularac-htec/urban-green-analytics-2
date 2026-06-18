"""Tests for the farm, infrastructure-type, and growing-system-type routers."""

from unittest.mock import MagicMock

import pytest

from app.routers.v1.farms.farm import get_farm_service
from app.routers.v1.farms.growing_system_type import get_growing_system_type_service
from app.routers.v1.farms.infrastructure_type import get_infrastructure_type_service
from app.services.farms.farm import FarmService
from app.services.farms.growing_system_type import GrowingSystemTypeService
from app.services.farms.infrastructure_type import InfrastructureTypeService
from tests.routers.conftest import RouteCase, assert_crud_endpoints

CASES = [
    RouteCase(
        name="farms",
        path="/api/v1/farms",
        dependency=get_farm_service,
        create_payload={
            "infrastructure_type_id": 1,
            "growing_system_type_id": 1,
            "name": "Farm",
            "city": "Belgrade",
            "size_m2": 100,
            "status": "ACTIVE",
            "growing_beds_count": 4,
        },
        update_payload={"name": "Renamed"},
    ),
    RouteCase(
        name="infrastructure-types",
        path="/api/v1/infrastructure-types",
        dependency=get_infrastructure_type_service,
        create_payload={"name": "Hydro", "description": "Soilless"},
        update_payload={"description": "Updated"},
    ),
    RouteCase(
        name="growing-system-types",
        path="/api/v1/growing-system-types",
        dependency=get_growing_system_type_service,
        create_payload={"name": "Vertical", "description": "Tower"},
        update_payload={"description": "Updated"},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_crud_endpoints(client, service, case):
    assert_crud_endpoints(client, service, case)


def test_get_farm_service_factory_constructs_service():
    assert isinstance(get_farm_service(MagicMock(), MagicMock(user_roles=[])), FarmService)


def test_get_infrastructure_type_service_factory_constructs_service():
    assert isinstance(get_infrastructure_type_service(MagicMock()), InfrastructureTypeService)


def test_get_growing_system_type_service_factory_constructs_service():
    assert isinstance(get_growing_system_type_service(MagicMock()), GrowingSystemTypeService)
