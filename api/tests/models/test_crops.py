"""Tests for the crop ORM models."""

from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory
from app.models.crops.farm_crop import FarmCrop


def test_crop_assigns_fields():
    crop = Crop(id=1, category_id=2, name="Basil", description="Herb")

    assert crop.id == 1
    assert crop.category_id == 2
    assert crop.name == "Basil"
    assert crop.description == "Herb"


def test_crop_category_assigns_fields():
    category = CropCategory(id=1, name="Herbs", description="Aromatic")

    assert category.id == 1
    assert category.name == "Herbs"
    assert category.description == "Aromatic"


def test_farm_crop_assigns_fields():
    farm_crop = FarmCrop(id=1, farm_id=2, crop_id=3, started_at=10, ended_at=20)

    assert farm_crop.farm_id == 2
    assert farm_crop.crop_id == 3
    assert farm_crop.started_at == 10
    assert farm_crop.ended_at == 20


def test_crop_category_relationship():
    category = CropCategory(id=1, name="Herbs")
    crop = Crop(id=1, category_id=1, name="Basil")

    crop.category = category

    assert crop.category is category
    assert list(category.crops) == [crop]
