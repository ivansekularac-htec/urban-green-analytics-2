from app.schemas.crops.crop import CropBase, CropCreate, CropResponse, CropUpdate


def test_crop_base():
    data = {
        "name": "Tomato",
        "category_id": 1,
    }

    crop = CropBase(**data)

    assert crop.name == "Tomato"


def test_crop_create():
    data = {
        "name": "Tomato",
        "category_id": 1,
    }

    crop = CropCreate(**data)

    assert crop.category_id == 1


def test_crop_update_partial():
    crop = CropUpdate(name="Updated Tomato")

    assert crop.name == "Updated Tomato"


def test_crop_response():
    data = {
        "id": 1,
        "name": "Tomato",
        "category_id": 1,
        "created_at": 1710000000,
        "updated_at": 1710000000,
    }

    crop = CropResponse(**data)

    assert crop.id == 1
