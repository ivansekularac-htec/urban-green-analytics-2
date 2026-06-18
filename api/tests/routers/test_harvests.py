"""Tests for the harvest and quality-grade routers."""

from unittest.mock import MagicMock

import pytest

from app.routers.v1.harvests.harvest import get_harvest_service
from app.routers.v1.harvests.quality_grade import get_quality_grade_service
from app.services.harvests.harvest import HarvestService
from app.services.harvests.quality_grade import QualityGradeService
from tests.routers.conftest import RouteCase, assert_crud_endpoints

CASES = [
    RouteCase(
        name="harvests",
        path="/api/v1/harvests",
        dependency=get_harvest_service,
        create_payload={
            "farm_id": 1,
            "crop_id": 1,
            "quality_grade_id": 1,
            "weight_kg": 5,
        },
        update_payload={"weight_kg": 6},
    ),
    RouteCase(
        name="quality-grades",
        path="/api/v1/quality-grades",
        dependency=get_quality_grade_service,
        create_payload={"code": "A", "name": "Premium", "description": "Top"},
        update_payload={"description": "Updated"},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_crud_endpoints(client, service, case):
    assert_crud_endpoints(client, service, case)


def test_get_harvest_service_factory_constructs_service():
    assert isinstance(get_harvest_service(MagicMock(), MagicMock(user_roles=[])), HarvestService)


def test_get_quality_grade_service_factory_constructs_service():
    assert isinstance(get_quality_grade_service(MagicMock()), QualityGradeService)
