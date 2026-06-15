from app.models.users.user_roles import UserRole


def test_user_role_model():
    ur = UserRole(
        user_id=1,
        role_id=2,
        farm_id=None,
        created_at=1000,
        updated_at=1000,
    )

    assert ur.user_id == 1
    assert ur.role_id == 2