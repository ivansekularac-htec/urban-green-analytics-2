"""Tests for the crop, crop-category, and farm-crop routers."""

from unittest.mock import MagicMock

import pytest

from app.routers.v1.crops.crop import get_crop_service
from app.routers.v1.crops.crop_category import get_crop_category_service
from app.routers.v1.crops.farm_crop import get_farm_crop_service
from app.services.crops.crop import CropService
from app.services.crops.crop_category import CropCategoryService
from app.services.crops.farm_crop import FarmCropService
from tests.routers.conftest import RouteCase, assert_crud_endpoints

CASES = [
    RouteCase(
        name="crops",
        path="/api/v1/crops",
        dependency=get_crop_service,
        create_payload={"name": "Basil", "description": "Herb", "category_id": 1},
        update_payload={"description": "Updated"},
    ),
    RouteCase(
        name="crop-categories",
        path="/api/v1/crop-categories",
        dependency=get_crop_category_service,
        create_payload={"name": "Herbs", "description": "Aromatic"},
        update_payload={"description": "Updated"},
    ),
    RouteCase(
        name="farm-crops",
        path="/api/v1/farm-crops",
        dependency=get_farm_crop_service,
        create_payload={"farm_id": 1, "crop_id": 1, "started_at": 1, "ended_at": 2},
        update_payload={"ended_at": 5},
    ),
]


@pytest.mark.parametrize("case", CASES, ids=[c.name for c in CASES])
def test_crud_endpoints(client, service, case):
    assert_crud_endpoints(client, service, case)


def test_get_crop_service_factory_constructs_service():
    assert isinstance(get_crop_service(MagicMock()), CropService)


def test_get_crop_category_service_factory_constructs_service():
    assert isinstance(get_crop_category_service(MagicMock()), CropCategoryService)


def test_get_farm_crop_service_factory_constructs_service():
    assert isinstance(get_farm_crop_service(MagicMock()), FarmCropService)
