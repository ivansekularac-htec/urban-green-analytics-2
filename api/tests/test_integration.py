"""
tests/test_integration.py
Integration tests for ORM models and Pydantic schemas.

This module verifies that all models can be imported, instantiated,
and work correctly with Pydantic schemas.
"""

from decimal import Decimal

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


# Test 1: Import all ORM models
def test_import_all_orm_models():
    """Verify all ORM models can be imported successfully."""
    from app.models import (
        Crop,
        CropCategory,
        Farm,
        FarmCrop,
        FarmInfrastructureType,
        FarmStatus,
        GrowingSystemType,
        Harvest,
        QualityGrade,
        Role,
        Sensor,
        SensorStatus,
        SensorType,
        User,
        UserRole,
    )

    # Verify models are not None
    assert Role is not None
    assert QualityGrade is not None
    assert FarmInfrastructureType is not None
    assert GrowingSystemType is not None
    assert CropCategory is not None
    assert Crop is not None
    assert SensorType is not None
    assert Sensor is not None
    assert User is not None
    assert UserRole is not None
    assert Farm is not None
    assert FarmCrop is not None
    assert Harvest is not None
    assert FarmStatus is not None
    assert SensorStatus is not None

    print("✓ All ORM models imported successfully")


# Test 2: Import all Pydantic schemas
def test_import_all_schemas():
    """Verify all Pydantic schemas can be imported successfully."""
    from app.schemas import (
        RoleBase,
        RoleCreate,
        RoleResponse,
        RoleUpdate,
    )

    # Verify schemas exist
    assert RoleBase is not None
    assert RoleCreate is not None
    assert RoleUpdate is not None
    assert RoleResponse is not None

    print("✓ All Pydantic schemas imported successfully")


# Test 3: Test RoleBase schema validation
def test_role_base_schema_validation():
    """Verify RoleBase schema validates data correctly."""
    from app.schemas import RoleBase

    # Valid data
    role_data = {"name": "Admin", "description": "Administrator role"}
    role = RoleBase(**role_data)
    assert role.name == "Admin"
    assert role.description == "Administrator role"

    print("✓ RoleBase schema validation works")


# Test 4: Test RoleUpdate schema with optional fields
def test_role_update_schema():
    """Verify RoleUpdate schema works with all-optional fields."""
    from app.schemas import RoleUpdate

    # Minimal update (only name)
    update1 = RoleUpdate(name="Super Admin")
    assert update1.name == "Super Admin"
    assert update1.description is None

    # Minimal update (only description)
    update2 = RoleUpdate(description="Updated description")
    assert update2.name is None
    assert update2.description == "Updated description"

    # Empty update (both None)
    update3 = RoleUpdate()
    assert update3.name is None
    assert update3.description is None

    print("✓ RoleUpdate schema works with optional fields")


# Test 5: Test Field max_length constraint
def test_field_max_length_constraint():
    """Verify Field max_length constraints work correctly."""
    from pydantic import ValidationError

    from app.schemas import RoleBase

    # Valid: within max_length
    valid_role = RoleBase(name="A" * 100, description="B" * 500)
    assert len(valid_role.name) == 100
    assert len(valid_role.description) == 500

    # Invalid: exceeds max_length for name
    try:
        RoleBase(name="A" * 101, description="Valid")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError as e:
        assert "String should have at most 100 characters" in str(e)

    # Invalid: exceeds max_length for description
    try:
        RoleBase(name="Valid", description="B" * 501)
        raise AssertionError("Should have raised ValidationError")
    except ValidationError as e:
        assert "String should have at most 500 characters" in str(e)

    print("✓ Field max_length constraints work correctly")


# Test 6: Test FarmUpdate schema with multiple optional fields
def test_farm_update_schema():
    """Verify FarmUpdate schema supports all-optional fields."""
    from app.schemas import FarmUpdate

    # Update only name
    update1 = FarmUpdate(name="New Farm Name")
    assert update1.name == "New Farm Name"
    assert update1.city is None
    assert update1.size_m2 is None

    # Update name and city
    update2 = FarmUpdate(name="Farm", city="Belgrade")
    assert update2.name == "Farm"
    assert update2.city == "Belgrade"
    assert update2.size_m2 is None

    # Update numeric field
    update3 = FarmUpdate(size_m2=Decimal("1000.50"))
    assert update3.size_m2 == Decimal("1000.50")
    assert update3.name is None

    print("✓ FarmUpdate schema works with optional fields")


# Test 7: Test SensorUpdate schema
def test_sensor_update_schema():
    """Verify SensorUpdate schema handles optional enum fields."""
    from app.models import SensorStatus
    from app.schemas import SensorUpdate

    # Update only serial_number
    update1 = SensorUpdate(serial_number="SENSOR-001")
    assert update1.serial_number == "SENSOR-001"
    assert update1.status is None

    # Update status enum
    update2 = SensorUpdate(status=SensorStatus.OFFLINE)
    assert update2.status == SensorStatus.OFFLINE
    assert update2.serial_number is None

    print("✓ SensorUpdate schema handles enum fields")


# Test 8: Test UserCreate schema with validation
def test_user_create_schema():
    """Verify UserCreate schema validates email and password."""
    from pydantic import ValidationError

    from app.schemas import UserCreate

    # Valid user
    user = UserCreate(
        email="test@example.com",
        full_name="John Doe",
        password="secure_password_123",
    )
    assert user.email == "test@example.com"
    assert user.full_name == "John Doe"

    # Invalid email
    try:
        UserCreate(
            email="invalid-email",
            full_name="John Doe",
            password="secure_password",
        )
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass

    print("✓ UserCreate schema validates email correctly")


# Test 9: Test HarvestCreate with Decimal fields
def test_harvest_create_schema():
    """Verify HarvestCreate schema handles Decimal fields."""
    from app.schemas import HarvestCreate

    harvest = HarvestCreate(
        farm_id=1,
        crop_id=1,
        quality_grade_id=1,
        weight_kg=Decimal("250.75"),
    )
    assert harvest.weight_kg == Decimal("250.75")

    print("✓ HarvestCreate schema handles Decimal fields")


# Test 10: Test CropCreate schema with optional fields
def test_crop_create_schema():
    """Verify CropCreate schema validates required and optional fields."""
    from app.schemas import CropCreate

    # Valid crop with description
    crop1 = CropCreate(
        category_id=1,
        name="Tomato",
        description="Red juicy tomato",
    )
    assert crop1.name == "Tomato"
    assert crop1.description == "Red juicy tomato"

    # Valid crop without description
    crop2 = CropCreate(category_id=1, name="Pepper", description=None)
    assert crop2.name == "Pepper"
    assert crop2.description is None

    print("✓ CropCreate schema handles optional fields")


# Test 11: Test UserRoleCreate schema
def test_user_role_create_schema():
    """Verify UserRoleCreate schema with optional farm_id."""
    from app.schemas import UserRoleCreate

    # Role without farm association
    role1 = UserRoleCreate(user_id=1, role_id=1, farm_id=None)
    assert role1.user_id == 1
    assert role1.role_id == 1
    assert role1.farm_id is None

    # Role with farm association
    role2 = UserRoleCreate(user_id=1, role_id=2, farm_id=5)
    assert role2.farm_id == 5

    print("✓ UserRoleCreate schema handles optional farm_id")


# Test 12: Test backward compatibility wrapper imports
def test_backward_compatibility_wrapper():
    """Verify backward compatibility wrapper schemas.py works."""
    from app.schemas import (
        FarmUpdate,
        HarvestUpdate,
        RoleCreate,
        RoleUpdate,
        UserUpdate,
    )

    # Verify imports work from wrapper
    assert RoleCreate is not None
    assert RoleUpdate is not None
    assert FarmUpdate is not None
    assert UserUpdate is not None
    assert HarvestUpdate is not None

    print("✓ Backward compatibility wrapper works")


# Test 13: Test enum imports from models
def test_enum_usage_in_schemas():
    """Verify enums can be used in schema validation."""
    from app.models import FarmStatus, SensorStatus
    from app.schemas import FarmCreate, SensorCreate

    # Farm with enum
    farm = FarmCreate(
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        status=FarmStatus.ACTIVE,
    )
    assert farm.status == FarmStatus.ACTIVE

    # Sensor with enum
    sensor = SensorCreate(
        farm_id=1,
        sensor_type_id=1,
        serial_number="SN-001",
        status=SensorStatus.ACTIVE,
    )
    assert sensor.status == SensorStatus.ACTIVE

    print("✓ Enum usage in schemas works correctly")


# Test 14: Test constraint max_length for all string types
def test_all_string_field_constraints():
    """Verify all schema string fields have proper max_length."""
    from pydantic import ValidationError

    from app.schemas import (
        CropCategoryBase,
        FarmBase,
        QualityGradeBase,
        SensorTypeBase,
    )

    # Test QualityGradeBase constraints
    try:
        QualityGradeBase(code="X" * 51, name="Valid", description="Valid")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass

    # Test CropCategoryBase constraints
    try:
        CropCategoryBase(name="X" * 101, description="Valid")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass

    # Test SensorTypeBase constraints
    try:
        SensorTypeBase(name="Valid", unit="X" * 51, description="Valid")
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass

    # Test FarmBase constraints
    try:
        FarmBase(
            infrastructure_type_id=1,
            growing_system_type_id=1,
            name="X" * 256,
            city="Valid",
        )
        raise AssertionError("Should have raised ValidationError")
    except ValidationError:
        pass

    print("✓ All string field constraints are properly applied")


if __name__ == "__main__":
    # Run tests manually
    test_import_all_orm_models()
    test_import_all_schemas()
    test_role_base_schema_validation()
    test_role_update_schema()
    test_field_max_length_constraint()
    test_farm_update_schema()
    test_sensor_update_schema()
    test_user_create_schema()
    test_harvest_create_schema()
    test_crop_create_schema()
    test_user_role_create_schema()
    test_backward_compatibility_wrapper()
    test_enum_usage_in_schemas()
    test_all_string_field_constraints()

    print("\n" + "=" * 50)
    print("✓ ALL TESTS PASSED!")
    print("=" * 50)
