from app.models.users.user import User


def test_user_model_creation():
    user = User(
        email="test@example.com",
        password_hash="hash",
        full_name="Test User",
        is_active=True,
        created_at=1000,
        updated_at=1000,
    )

    assert user.email == "test@example.com"
    assert user.is_active is True
