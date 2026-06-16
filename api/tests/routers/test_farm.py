from unittest.mock import patch

from app.models.farms.farm import Farm
from app.models.farms.farm_status import FarmStatus


@patch("app.routers.farms.farm.farm_crud.create")
def test_create_farm(
    mock_create,
    client,
):
    mock_create.return_value = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        status=FarmStatus.ACTIVE,
    )

    response = client.post(
        "/farm/",
        json={
            "infrastructure_type_id": 1,
            "growing_system_type_id": 1,
            "name": "Test Farm",
        },
    )

    assert response.status_code == 201


def test_create_farm_validation_error(
    client,
):
    response = client.post(
        "/farm/",
        json={},
    )

    assert response.status_code == 422


@patch("app.routers.farms.farm.farm_crud.get")
def test_get_farm(
    mock_get,
    client,
):
    mock_get.return_value = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Test Farm",
        status=FarmStatus.ACTIVE,
    )

    response = client.get("/farm/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1


@patch("app.routers.farms.farm.farm_crud.get")
def test_get_farm_not_found(
    mock_get,
    client,
):
    mock_get.return_value = None

    response = client.get("/farm/999")

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Farm not found",
    }


@patch("app.routers.farms.farm.farm_crud.get_all")
def test_get_farms(
    mock_get_all,
    client,
):
    mock_get_all.return_value = [
        Farm(
            id=1,
            infrastructure_type_id=1,
            growing_system_type_id=1,
            name="Farm",
            status=FarmStatus.ACTIVE,
        )
    ]

    response = client.get("/farm/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1


@patch("app.routers.farms.farm.farm_crud.update")
@patch("app.routers.farms.farm.farm_crud.get")
def test_update_farm(
    mock_get,
    mock_update,
    client,
):
    farm = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )

    mock_get.return_value = farm

    farm.name = "Updated Farm"

    mock_update.return_value = farm

    response = client.put(
        "/farm/1",
        json={
            "name": "Updated Farm",
        },
    )

    assert response.status_code == 200


@patch("app.routers.farms.farm.farm_crud.get")
def test_update_farm_not_found(
    mock_get,
    client,
):
    mock_get.return_value = None

    response = client.put(
        "/farm/999",
        json={
            "name": "Updated Farm",
        },
    )

    assert response.status_code == 404


@patch("app.routers.farms.farm.farm_crud.delete")
@patch("app.routers.farms.farm.farm_crud.get")
def test_delete_farm(
    mock_get,
    mock_delete,
    client,
):
    mock_get.return_value = Farm(
        id=1,
        infrastructure_type_id=1,
        growing_system_type_id=1,
        name="Farm",
        status=FarmStatus.ACTIVE,
    )

    response = client.delete("/farm/1")

    assert response.status_code == 204

    mock_delete.assert_called_once()


@patch("app.routers.farms.farm.farm_crud.get")
def test_delete_farm_not_found(
    mock_get,
    client,
):
    mock_get.return_value = None

    response = client.delete("/farm/999")

    assert response.status_code == 404
