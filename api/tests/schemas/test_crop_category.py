from app.schemas.crops.crop_category import (
    CropCategoryBase,
    CropCategoryCreate,
    CropCategoryResponse,
)


def test_crop_category_base():
    data = {"name": "Vegetables"}

    cat = CropCategoryBase(**data)

    assert cat.name == "Vegetables"


def test_crop_category_create():
    cat = CropCategoryCreate(name="Vegetables")

    assert cat.name == "Vegetables"


def test_crop_category_response():
    data = {
        "id": 1,
        "name": "Vegetables",
        "created_at": 1710000000,
        "updated_at": 1710000000,
    }

    cat = CropCategoryResponse(**data)

    assert cat.id == 1
