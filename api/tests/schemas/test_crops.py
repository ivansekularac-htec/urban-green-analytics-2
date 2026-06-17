"""Tests for crop, crop-category, and farm-crop schemas."""

from app.schemas.crops.crop import CropCreate, CropResponse, CropUpdate
from app.schemas.crops.crop_category import (
    CropCategoryCreate,
    CropCategoryResponse,
    CropCategoryUpdate,
)
from app.schemas.crops.farm_crop import FarmCropCreate, FarmCropResponse, FarmCropUpdate


def test_crop_create_accepts_full_payload():
    create = CropCreate(name="Basil", description="Herb", category_id=1)

    assert create.name == "Basil"
    assert create.category_id == 1


def test_crop_update_accepts_partial_payload():
    update = CropUpdate(name="Basil")

    assert update.name == "Basil"
    assert update.category_id is None


def test_crop_response_assigns_id_and_audit_fields():
    response = CropResponse(
        id=1,
        name="Basil",
        description="Herb",
        category_id=1,
        created_at=1,
        updated_at=2,
    )

    assert response.id == 1


def test_crop_category_create_and_update():
    create = CropCategoryCreate(name="Herbs", description="Aromatic")
    update = CropCategoryUpdate(description="Updated")

    assert create.name == "Herbs"
    assert update.description == "Updated"


def test_crop_category_response_round_trip():
    response = CropCategoryResponse(
        id=1,
        name="Herbs",
        description="Aromatic",
        created_at=1,
        updated_at=2,
    )

    assert response.id == 1


def test_farm_crop_create_and_update():
    create = FarmCropCreate(farm_id=1, crop_id=2, started_at=10, ended_at=20)
    update = FarmCropUpdate(ended_at=99)

    assert create.farm_id == 1
    assert create.ended_at == 20
    assert update.ended_at == 99


def test_farm_crop_response_round_trip():
    response = FarmCropResponse(
        id=1,
        farm_id=1,
        crop_id=2,
        started_at=10,
        ended_at=20,
        created_at=1,
        updated_at=2,
    )

    assert response.farm_id == 1
