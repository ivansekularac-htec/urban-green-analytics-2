"""Tests for crop-related services.

Each service is a thin ``BaseService`` subclass that only sets the
``entity_name`` used in error messages. CRUD behaviour itself is covered
in ``tests/services/test_base``.
"""

from unittest.mock import MagicMock

from app.services.crops.crop import CropService
from app.services.crops.crop_category import CropCategoryService
from app.services.crops.farm_crop import FarmCropService


def test_crop_service_uses_expected_entity_name():
    assert CropService(MagicMock()).entity_name == "Crop"


def test_crop_category_service_uses_expected_entity_name():
    assert CropCategoryService(MagicMock()).entity_name == "Crop category"


def test_farm_crop_service_uses_expected_entity_name():
    assert FarmCropService(MagicMock(), MagicMock(user_roles=[])).entity_name == "Farm crop"
