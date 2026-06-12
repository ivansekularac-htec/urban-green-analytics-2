from app.models.farm import Farm
from app.models.role import Role
from app.models.sensor import Sensor
from app.models.user import User
from app.schemas.role import RoleResponse


def test_models_import():
    assert Farm is not None
    assert User is not None
    assert Sensor is not None
    assert Role is not None


def test_farm_has_sensor_relationship():
    assert "sensors" in Farm.__mapper__.relationships


def test_sensor_has_farm_relationship():
    assert "farm" in Sensor.__mapper__.relationships


def test_role_response_from_model():
    role = Role(
        id=1,
        name="Admin",
        description="Administrator role",
        created_at=100,
        updated_at=100,
    )

    response = RoleResponse.model_validate(role)

    assert response.id == 1
    assert response.name == "Admin"
    assert response.description == "Administrator role"
    assert response.created_at == 100
    assert response.updated_at == 100
