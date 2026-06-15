from app.models.crops.crop import Crop
from app.models.crops.crop_category import CropCategory


def test_crop_model():
    category = CropCategory(
        name="Vegetables",
    )

    crop = Crop(
        category_id=1,
        name="Tomato",
        description=None,
    )

    assert crop.name == "Tomato"