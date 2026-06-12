import pytest
from pydantic import ValidationError

from app.enums import FarmStatus
from app.schemas.farm import FarmCreate
from app.schemas.role import RoleCreate
from app.schemas.user import UserCreate


def test_user_schema():
    user = UserCreate(
        email="test@test.com",
        full_name="John Doe",
        password="password123",
    )

    assert user.email == "test@test.com"
    assert user.full_name == "John Doe"


def test_farm_schema():
    farm = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        city="Berlin",
        status=FarmStatus.ACTIVE,
    )

    assert farm.name == "Test Farm"
    assert farm.city == "Berlin"
    assert farm.status == FarmStatus.ACTIVE


def test_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(
            email="invalid-email",
            full_name="John Doe",
            password="password123",
        )


def test_role_name_too_long():
    with pytest.raises(ValidationError):
        RoleCreate(
            name="a" * 101,
        )


def test_missing_required_field():
    with pytest.raises(ValidationError):
        FarmCreate(
            infrastructure_type_id=1,
            growing_system_type_id=1,
            city="Berlin",
            status=FarmStatus.ACTIVE,
        )
