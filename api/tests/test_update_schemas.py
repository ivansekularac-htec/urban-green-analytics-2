"""
tests/test_update_schemas.py
Tests for CRUD Update schemas with all-optional fields.

This module verifies that Update schemas support partial updates
for PATCH operations and work correctly with the rest of the API.
"""

from decimal import Decimal

try:
    import pytest

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False


def test_role_update_all_combinations():
    """Test RoleUpdate with all possible field combinations."""
    from app.schemas import RoleUpdate

    # Empty update
    update1 = RoleUpdate()
    assert update1.name is None
    assert update1.description is None

    # Only name
    update2 = RoleUpdate(name="Viewer")
    assert update2.name == "Viewer"
    assert update2.description is None

    # Only description
    update3 = RoleUpdate(description="Read-only access")
    assert update3.name is None
    assert update3.description == "Read-only access"

    # Both fields
    update4 = RoleUpdate(name="Editor", description="Can edit content")
    assert update4.name == "Editor"
    assert update4.description == "Can edit content"

    print("✓ RoleUpdate supports all field combinations")


def test_farm_update_all_fields():
    """Test FarmUpdate with all possible fields."""
    from app.models import FarmStatus
    from app.schemas import FarmUpdate

    # Multiple field update
    update = FarmUpdate(
        name="Expanded Farm",
        city="Novi Sad",
        size_m2=Decimal("10000.00"),
        status=FarmStatus.MAINTENANCE,
        growing_beds_count=50,
    )

    assert update.name == "Expanded Farm"
    assert update.city == "Novi Sad"
    assert update.size_m2 == Decimal("10000.00")
    assert update.status == FarmStatus.MAINTENANCE
    assert update.growing_beds_count == 50

    # Partial update
    update2 = FarmUpdate(city="Belgrade")
    assert update2.city == "Belgrade"
    assert update2.name is None
    assert update2.size_m2 is None

    print("✓ FarmUpdate handles all field combinations")


def test_user_update_password_change():
    """Test UserUpdate specifically for password changes."""
    from app.schemas import UserUpdate

    # Update password only
    update1 = UserUpdate(password="new_secure_password_123")
    assert update1.password == "new_secure_password_123"
    assert update1.email is None
    assert update1.full_name is None
    assert update1.is_active is None

    # Update email only
    update2 = UserUpdate(email="newemail@example.com")
    assert update2.email == "newemail@example.com"
    assert update2.password is None

    # Update is_active status only
    update3 = UserUpdate(is_active=False)
    assert update3.is_active is False
    assert update3.password is None
    assert update3.email is None

    print("✓ UserUpdate supports password and status changes")


def test_sensor_update_status_change():
    """Test SensorUpdate for status changes."""
    from app.models import SensorStatus
    from app.schemas import SensorUpdate

    # Update status to OFFLINE
    update1 = SensorUpdate(status=SensorStatus.OFFLINE)
    assert update1.status == SensorStatus.OFFLINE
    assert update1.serial_number is None
    assert update1.farm_id is None

    # Update status to MAINTENANCE
    update2 = SensorUpdate(status=SensorStatus.MAINTENANCE)
    assert update2.status == SensorStatus.MAINTENANCE

    # Update serial number
    update3 = SensorUpdate(serial_number="UPDATED-SN-001")
    assert update3.serial_number == "UPDATED-SN-001"
    assert update3.status is None

    print("✓ SensorUpdate supports status changes")


def test_crop_update_category_change():
    """Test CropUpdate for moving crops between categories."""
    from app.schemas import CropUpdate

    # Move crop to different category
    update = CropUpdate(category_id=5)
    assert update.category_id == 5
    assert update.name is None
    assert update.description is None

    # Update name
    update2 = CropUpdate(name="Cherry Tomato")
    assert update2.name == "Cherry Tomato"
    assert update2.category_id is None

    # Update description
    update3 = CropUpdate(description="Small sweet tomatoes")
    assert update3.description == "Small sweet tomatoes"

    print("✓ CropUpdate supports category and field updates")


def test_harvest_update_weight():
    """Test HarvestUpdate for weight corrections."""
    from app.schemas import HarvestUpdate

    # Correct weight
    update1 = HarvestUpdate(weight_kg=Decimal("275.50"))
    assert update1.weight_kg == Decimal("275.50")
    assert update1.farm_id is None
    assert update1.quality_grade_id is None

    # Update quality grade
    update2 = HarvestUpdate(quality_grade_id=2)
    assert update2.quality_grade_id == 2
    assert update2.weight_kg is None

    # Update multiple fields
    update3 = HarvestUpdate(
        weight_kg=Decimal("300.00"),
        quality_grade_id=1,
    )
    assert update3.weight_kg == Decimal("300.00")
    assert update3.quality_grade_id == 1

    print("✓ HarvestUpdate supports weight corrections")


def test_quality_grade_update():
    """Test QualityGradeUpdate for grade modifications."""
    from app.schemas import QualityGradeUpdate

    # Update code
    update1 = QualityGradeUpdate(code="AA")
    assert update1.code == "AA"
    assert update1.name is None

    # Update name
    update2 = QualityGradeUpdate(name="Premium Grade")
    assert update2.name == "Premium Grade"

    # Update description
    update3 = QualityGradeUpdate(
        description="Premium quality products",
    )
    assert update3.description == "Premium quality products"
    assert update3.code is None

    print("✓ QualityGradeUpdate works correctly")


def test_sensor_type_update():
    """Test SensorTypeUpdate for sensor type modifications."""
    from app.schemas import SensorTypeUpdate

    # Update unit (unlikely but possible)
    update1 = SensorTypeUpdate(unit="Celsius")
    assert update1.unit == "Celsius"
    assert update1.name is None

    # Update optimal ranges
    update2 = SensorTypeUpdate(
        optimal_min=Decimal("20.0"),
        optimal_max=Decimal("30.0"),
    )
    assert update2.optimal_min == Decimal("20.0")
    assert update2.optimal_max == Decimal("30.0")

    print("✓ SensorTypeUpdate works correctly")


def test_growing_system_type_update():
    """Test GrowingSystemTypeUpdate."""
    from app.schemas import GrowingSystemTypeUpdate

    update = GrowingSystemTypeUpdate(
        name="Advanced Hydroponic System",
        description="NFT hydroponic with automation",
    )
    assert update.name == "Advanced Hydroponic System"
    assert update.description == "NFT hydroponic with automation"

    print("✓ GrowingSystemTypeUpdate works correctly")


def test_farm_infrastructure_type_update():
    """Test FarmInfrastructureTypeUpdate."""
    from app.schemas import FarmInfrastructureTypeUpdate

    update = FarmInfrastructureTypeUpdate(
        name="Poly Tunnel",
        description="Lightweight plastic covered tunnel",
    )
    assert update.name == "Poly Tunnel"
    assert update.description == "Lightweight plastic covered tunnel"

    print("✓ FarmInfrastructureTypeUpdate works correctly")


def test_crop_category_update():
    """Test CropCategoryUpdate."""
    from app.schemas import CropCategoryUpdate

    # Update name
    update1 = CropCategoryUpdate(name="Root Vegetables")
    assert update1.name == "Root Vegetables"
    assert update1.description is None

    # Update description
    update2 = CropCategoryUpdate(description="Vegetables grown underground")
    assert update2.description == "Vegetables grown underground"

    # Update both
    update3 = CropCategoryUpdate(
        name="Legumes",
        description="Bean and pea crops",
    )
    assert update3.name == "Legumes"
    assert update3.description == "Bean and pea crops"

    print("✓ CropCategoryUpdate works correctly")


def test_farm_crop_update():
    """Test FarmCropUpdate for lifecycle changes."""
    from app.schemas import FarmCropUpdate

    # End a crop season
    update = FarmCropUpdate(ended_at=1234567999)
    assert update.ended_at == 1234567999
    assert update.started_at is None
    assert update.farm_id is None

    # Change farm (unlikely but possible)
    update2 = FarmCropUpdate(farm_id=2)
    assert update2.farm_id == 2

    print("✓ FarmCropUpdate handles lifecycle changes")


def test_user_role_update():
    """Test UserRoleUpdate for permission modifications."""
    from app.schemas import UserRoleUpdate

    # Change role assignment
    update1 = UserRoleUpdate(role_id=3)
    assert update1.role_id == 3
    assert update1.user_id is None
    assert update1.farm_id is None

    # Add farm association to existing role
    update2 = UserRoleUpdate(farm_id=5)
    assert update2.farm_id == 5

    # Remove farm association (set to None would require explicit handling)
    update3 = UserRoleUpdate(farm_id=None)
    assert update3.farm_id is None

    print("✓ UserRoleUpdate handles permission modifications")


def test_update_schema_constraint_validation():
    """Verify Update schemas also enforce max_length constraints."""
    from pydantic import ValidationError

    from app.schemas import FarmUpdate, RoleUpdate

    # Valid update within constraints
    valid_update = RoleUpdate(name="X" * 100)
    assert len(valid_update.name) == 100

    # Invalid update exceeds constraints
    try:
        RoleUpdate(name="X" * 101)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at most 100 characters" in str(e)

    # Valid farm city update
    valid_farm_update = FarmUpdate(city="X" * 255)
    assert len(valid_farm_update.city) == 255

    # Invalid farm city update
    try:
        FarmUpdate(city="X" * 256)
        assert False, "Should have raised ValidationError"
    except ValidationError as e:
        assert "String should have at most 255 characters" in str(e)

    print("✓ Update schemas enforce max_length constraints")


def test_update_schemas_preserve_data_types():
    """Verify Update schemas preserve correct data types."""
    from app.models import FarmStatus
    from app.schemas import (
        CropUpdate,
        FarmUpdate,
        HarvestUpdate,
    )

    # Decimal preservation
    harvest_update = HarvestUpdate(weight_kg=Decimal("123.45"))
    assert isinstance(harvest_update.weight_kg, Decimal)
    assert harvest_update.weight_kg == Decimal("123.45")

    # Enum preservation
    farm_update = FarmUpdate(status=FarmStatus.MAINTENANCE)
    assert farm_update.status == FarmStatus.MAINTENANCE
    assert isinstance(farm_update.status, FarmStatus)

    # Int preservation
    crop_update = CropUpdate(category_id=42)
    assert isinstance(crop_update.category_id, int)
    assert crop_update.category_id == 42

    print("✓ Update schemas preserve data types correctly")


if __name__ == "__main__":
    # Run tests manually
    test_role_update_all_combinations()
    test_farm_update_all_fields()
    test_user_update_password_change()
    test_sensor_update_status_change()
    test_crop_update_category_change()
    test_harvest_update_weight()
    test_quality_grade_update()
    test_sensor_type_update()
    test_growing_system_type_update()
    test_farm_infrastructure_type_update()
    test_crop_category_update()
    test_farm_crop_update()
    test_user_role_update()
    test_update_schema_constraint_validation()
    test_update_schemas_preserve_data_types()

    print("\n" + "=" * 50)
    print("✓ ALL UPDATE SCHEMA TESTS PASSED!")
    print("=" * 50)
