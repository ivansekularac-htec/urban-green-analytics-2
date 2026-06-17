"""Tests for crop-related repositories.

Each repository is a thin ``BaseRepository`` subclass that only configures
its ORM model. CRUD behaviour is covered in ``tests/repositories/test_base``.
"""

from unittest.mock import MagicMock

from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory
from app.models.crops.farm_crop import FarmCrop
from app.repositories.crops.crop import CropRepository
from app.repositories.crops.crop_category import CropCategoryRepository
from app.repositories.crops.farm_crop import FarmCropRepository


def test_crop_repository_binds_crop_model():
    assert CropRepository(MagicMock()).model is Crop


def test_crop_category_repository_binds_crop_category_model():
    assert CropCategoryRepository(MagicMock()).model is CropCategory


def test_farm_crop_repository_binds_farm_crop_model():
    assert FarmCropRepository(MagicMock()).model is FarmCrop
