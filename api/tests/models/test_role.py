from app.models.users.role import Role


def test_role_creation():
    role = Role(
        id=1,
        name="ADMIN",
        description="Administrator",
        created_at=1000,
        updated_at=1000,
    )

    assert role.name == "ADMIN"