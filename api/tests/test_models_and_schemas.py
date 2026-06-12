from app.enums import FarmStatus
from app.models import (
    Farm,
    Sensor,
    User,
)
from app.schemas import (
    FarmCreate,
    UserCreate,
)


def test_user_schema():
    user = UserCreate(
        email="test@test.com",
        full_name="John Doe",
        password="password123",
    )

    assert user.email == "test@test.com"


def test_farm_schema():
    farm = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        city="Berlin",
        status=FarmStatus.ACTIVE,
    )

    assert farm.name == "Test Farm"


def test_models_import():
    assert Farm is not None
    assert User is not None
    assert Sensor is not None
