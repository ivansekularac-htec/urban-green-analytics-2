from app.models.users.user import User
from app.schemas.users.user import UserResponse
from app.models.users.role import Role
from app.models.users.user_roles import UserRole


def test_user_model_to_schema_flow():
    user = User(
        id=1,
        email="test@example.com",
        password_hash="hash",
        full_name="Test User",
        is_active=True,
        created_at=1000,
        updated_at=2000,
    )

    schema = UserResponse.model_validate(user)

    assert schema.id == 1
    assert schema.email == "test@example.com"
    assert schema.is_active is True


def test_user_role_relationship():
    user = User(
        id=1,
        email="test@example.com",
        password_hash="hash",
        full_name="Test User",
        is_active=True,
        created_at=1000,
        updated_at=1000,
    )

    role = Role(
        id=1,
        name="ADMIN",
        description="Administrator",
        created_at=1000,
        updated_at=1000,
    )

    user_role = UserRole(
        id=1,
        user=user,
        role=role,
        created_at=1000,
        updated_at=1000,
    )

    assert user_role.user == user
    assert user_role.role == role