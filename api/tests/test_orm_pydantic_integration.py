"""
tests/test_orm_pydantic_integration.py
Tests for integration between SQLAlchemy ORM models and Pydantic schemas.

This module verifies that ORM model instances can be validated against
Pydantic schemas and vice versa.
"""

from decimal import Decimal

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


def test_role_model_to_schema():
    """Verify ORM Role model can be converted to Pydantic schema."""
    from app.models import Role
    from app.schemas import RoleResponse

    # Create a mock Role instance (with mocked attributes)
    role = Role(
        id=1,
        name="Admin",
        description="Administrator role",
        created_at=1234567890,
        updated_at=1234567890,
    )

    # Convert to Pydantic schema
    role_response = RoleResponse.model_validate(role)

    assert role_response.id == 1
    assert role_response.name == "Admin"
    assert role_response.description == "Administrator role"
    assert role_response.created_at == 1234567890
    assert role_response.updated_at == 1234567890

    print("✓ ORM Role model converts to Pydantic schema")


def test_user_create_schema_to_model_fields():
    """Verify UserCreate schema fields match what ORM User expects."""
    from app.schemas import UserCreate

    user_data = UserCreate(
        email="john@example.com",
        full_name="John Doe",
        password="secure_password_123",
        is_active=True,
    )

    assert user_data.email == "john@example.com"
    assert user_data.full_name == "John Doe"
    assert user_data.password == "secure_password_123"
    assert user_data.is_active is True

    print("✓ UserCreate schema fields are correctly defined")


def test_farm_create_schema_validation():
    """Verify FarmCreate schema validates all required fields."""
    from app.models import FarmStatus
    from app.schemas import FarmCreate

    farm = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Urban Farm",
        city="Belgrade",
        size_m2=Decimal("5000.00"),
        status=FarmStatus.ACTIVE,
    )

    assert farm.infrastructure_type_id == 1
    assert farm.growing_system_type_id == 1
    assert farm.name == "Urban Farm"
    assert farm.city == "Belgrade"
    assert farm.size_m2 == Decimal("5000.00")
    assert farm.status == FarmStatus.ACTIVE

    print("✓ FarmCreate schema validates all fields correctly")


def test_sensor_enum_conversion():
    """Verify sensor status enum works between model and schema."""
    from app.models import SensorStatus
    from app.schemas import SensorCreate, SensorUpdate

    # Create sensor with enum
    sensor_create = SensorCreate(
        farm_id=1,
        sensor_type_id=1,
        serial_number="TEMP-001",
        status=SensorStatus.ACTIVE,
        installed_at=1234567890,
    )

    assert sensor_create.status == SensorStatus.ACTIVE
    assert sensor_create.status.value == "ACTIVE"

    # Update sensor status to OFFLINE
    sensor_update = SensorUpdate(status=SensorStatus.OFFLINE)
    assert sensor_update.status == SensorStatus.OFFLINE
    assert sensor_update.status.value == "OFFLINE"

    print("✓ Sensor enum conversion works correctly")


def test_harvest_decimal_handling():
    """Verify Harvest schema handles Decimal fields correctly."""
    from app.schemas import HarvestCreate, HarvestUpdate

    # Create harvest with Decimal
    harvest = HarvestCreate(
        farm_id=1,
        crop_id=1,
        quality_grade_id=1,
        weight_kg=Decimal("250.75"),
    )

    assert harvest.weight_kg == Decimal("250.75")
    assert isinstance(harvest.weight_kg, Decimal)

    # Update with different Decimal
    update = HarvestUpdate(weight_kg=Decimal("100.25"))
    assert update.weight_kg == Decimal("100.25")

    print("✓ Harvest Decimal handling works correctly")


def test_optional_fields_in_update_schemas():
    """Verify Update schemas allow partial updates."""
    from app.schemas import (
        CropUpdate,
        FarmUpdate,
        HarvestUpdate,
        SensorUpdate,
        UserUpdate,
    )

    # FarmUpdate - only name
    farm_update = FarmUpdate(name="New Name")
    assert farm_update.name == "New Name"
    assert farm_update.city is None
    assert farm_update.size_m2 is None

    # UserUpdate - empty update
    user_update = UserUpdate()
    assert user_update.email is None
    assert user_update.full_name is None
    assert user_update.password is None

    # CropUpdate - category and name
    crop_update = CropUpdate(category_id=2, name="Lettuce")
    assert crop_update.category_id == 2
    assert crop_update.name == "Lettuce"
    assert crop_update.description is None

    # SensorUpdate - only status
    sensor_update = SensorUpdate()
    assert sensor_update.farm_id is None
    assert sensor_update.serial_number is None

    # HarvestUpdate - only weight
    harvest_update = HarvestUpdate(weight_kg=Decimal("500.00"))
    assert harvest_update.weight_kg == Decimal("500.00")
    assert harvest_update.farm_id is None

    print("✓ Update schemas support partial updates correctly")


def test_schema_validation_with_constraints():
    """Verify schema constraints prevent invalid data."""
    from pydantic import ValidationError

    from app.schemas import RoleBase

    # Valid data
    valid_role = RoleBase(name="Editor", description="Content editor")
    assert valid_role.name == "Editor"

    # Invalid: name too long
    try:
        RoleBase(name="X" * 101, description="Valid")
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at most 100 characters" in str(e)

    # Invalid: description too long
    try:
        RoleBase(name="Valid", description="Y" * 501)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at most 500 characters" in str(e)

    print("✓ Schema validation constraints work correctly")


def test_crop_category_with_crop():
    """Verify CropCategory and Crop schemas work together."""
    from app.schemas import CropCategoryCreate, CropCreate

    # Create category
    category = CropCategoryCreate(
        name="Vegetables",
        description="Green leafy vegetables",
    )
    assert category.name == "Vegetables"

    # Create crop under category (would reference category_id)
    crop = CropCreate(
        category_id=1,  # Would reference the created category
        name="Tomato",
        description="Red garden tomato",
    )
    assert crop.category_id == 1
    assert crop.name == "Tomato"

    print("✓ CropCategory and Crop schemas work together")


def test_user_role_relationship():
    """Verify UserRole schema handles user-role relationships."""
    from app.schemas import UserRoleCreate, UserRoleUpdate

    # User role without farm (global role)
    global_role = UserRoleCreate(user_id=1, role_id=2, farm_id=None)
    assert global_role.user_id == 1
    assert global_role.role_id == 2
    assert global_role.farm_id is None

    # User role with farm (farm-specific role)
    farm_role = UserRoleCreate(user_id=1, role_id=3, farm_id=5)
    assert farm_role.farm_id == 5

    # Update to add farm association
    update = UserRoleUpdate(farm_id=10)
    assert update.farm_id == 10
    assert update.user_id is None
    assert update.role_id is None

    print("✓ UserRole relationship schemas work correctly")


def test_farm_crop_association():
    """Verify FarmCrop schema handles association correctly."""
    from app.schemas import FarmCropCreate, FarmCropUpdate

    # Create farm-crop association
    farm_crop = FarmCropCreate(
        farm_id=1,
        crop_id=2,
        started_at=1234567890,
        ended_at=None,
    )

    assert farm_crop.farm_id == 1
    assert farm_crop.crop_id == 2
    assert farm_crop.started_at == 1234567890
    assert farm_crop.ended_at is None

    # Update association (e.g., mark as ended)
    update = FarmCropUpdate(ended_at=1234567999)
    assert update.ended_at == 1234567999
    assert update.started_at is None

    print("✓ FarmCrop association schema works correctly")


def test_email_validation():
    """Verify email field validation in UserCreate."""
    from pydantic import ValidationError

    from app.schemas import UserCreate

    # Valid email
    user = UserCreate(
        email="user@example.com",
        full_name="User Name",
        password="password123",
    )
    assert user.email == "user@example.com"

    # Invalid email format
    try:
        UserCreate(
            email="not-an-email",
            full_name="User Name",
            password="password123",
        )
        assert False, "Should have raised ValidationError"
    except ValidationError:
        pass

    print("✓ Email validation works correctly")


def test_all_create_schemas_instantiate():
    """Verify all Create schemas can be instantiated successfully."""
    from app.models import FarmStatus, SensorStatus
    from app.schemas import (
        CropCategoryCreate,
        CropCreate,
        FarmCreate,
        FarmCropCreate,
        FarmInfrastructureTypeCreate,
        GrowingSystemTypeCreate,
        HarvestCreate,
        QualityGradeCreate,
        RoleCreate,
        SensorCreate,
        SensorTypeCreate,
        UserCreate,
        UserRoleCreate,
    )

    # Role
    RoleCreate(name="Admin", description="Admin role")

    # Quality Grade
    QualityGradeCreate(code="A", name="Grade A", description="Best quality")

    # Infrastructure Type
    FarmInfrastructureTypeCreate(name="Greenhouse", description="Glass greenhouse")

    # Growing System Type
    GrowingSystemTypeCreate(name="Hydroponic", description="Water-based system")

    # Crop Category
    CropCategoryCreate(name="Vegetables", description="Vegetable category")

    # Crop
    CropCreate(category_id=1, name="Tomato", description="Red tomato")

    # Sensor Type
    SensorTypeCreate(name="Temperature", unit="°C", description="Temp sensor")

    # Sensor
    SensorCreate(farm_id=1, sensor_type_id=1, serial_number="SN-001", status=SensorStatus.ACTIVE)

    # User
    UserCreate(email="user@example.com", full_name="User", password="pass123")

    # User Role
    UserRoleCreate(user_id=1, role_id=1, farm_id=None)

    # Farm
    FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        status=FarmStatus.ACTIVE,
    )

    # Farm Crop
    FarmCropCreate(farm_id=1, crop_id=1, started_at=1234567890)

    # Harvest
    HarvestCreate(
        farm_id=1,
        crop_id=1,
        quality_grade_id=1,
        weight_kg=Decimal("100.00"),
    )

    print("✓ All Create schemas instantiate successfully")


if __name__ == "__main__":
    # Run tests manually
    test_role_model_to_schema()
    test_user_create_schema_to_model_fields()
    test_farm_create_schema_validation()
    test_sensor_enum_conversion()
    test_harvest_decimal_handling()
    test_optional_fields_in_update_schemas()
    test_schema_validation_with_constraints()
    test_crop_category_with_crop()
    test_user_role_relationship()
    test_farm_crop_association()
    test_email_validation()
    test_all_create_schemas_instantiate()

    print("\n" + "=" * 50)
    print("✓ ALL ORM-PYDANTIC INTEGRATION TESTS PASSED!")
    print("=" * 50)
