from app.schemas.crops.crop import CropBase, CropCreate


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
