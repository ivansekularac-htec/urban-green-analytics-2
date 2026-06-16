"""
test_infrastructure_types.py
Tests for farm infrastructure type CRUD endpoints.
"""


def test_create_farm_infrastructure_type(client):
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Hydroponic",
            "description": "Water-based growing infrastructure",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hydroponic"
    assert data["description"] == "Water-based growing infrastructure"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_farm_infrastructure_type_invalid_input(client):
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "description": "Missing required name",
        },
    )

    assert response.status_code == 422


def test_get_farm_infrastructure_types(client):
    client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Aeroponic",
            "description": "Mist-based growing infrastructure",
        },
    )

    response = client.get("/api/v1/farm-infrastructure-types")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Aeroponic"
    assert data[0]["description"] == "Mist-based growing infrastructure"


def test_get_farm_infrastructure_type(client):
    create_response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Vertical Hydroponic",
            "description": "Vertical hydroponic setup",
        },
    )

    infrastructure_type_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/farm-infrastructure-types/{infrastructure_type_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == infrastructure_type_id
    assert data["name"] == "Vertical Hydroponic"
    assert data["description"] == "Vertical hydroponic setup"


def test_get_farm_infrastructure_type_not_found(client):
    response = client.get("/api/v1/farm-infrastructure-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm infrastructure type not found."


def test_update_farm_infrastructure_type(client):
    create_response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Old Infrastructure",
            "description": "Old description",
        },
    )

    infrastructure_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farm-infrastructure-types/{infrastructure_type_id}",
        json={
            "name": "Updated Infrastructure",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == infrastructure_type_id
    assert data["name"] == "Updated Infrastructure"
    assert data["description"] == "Updated description"


def test_update_farm_infrastructure_type_partial(client):
    create_response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Partial Infrastructure",
            "description": "Original description",
        },
    )

    infrastructure_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farm-infrastructure-types/{infrastructure_type_id}",
        json={
            "description": "Partially updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Partial Infrastructure"
    assert data["description"] == "Partially updated description"


def test_update_farm_infrastructure_type_not_found(client):
    response = client.put(
        "/api/v1/farm-infrastructure-types/999",
        json={
            "name": "Missing Infrastructure",
            "description": "Missing description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm infrastructure type not found."


def test_delete_farm_infrastructure_type(client):
    create_response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Delete Infrastructure",
            "description": "To be deleted",
        },
    )

    infrastructure_type_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/farm-infrastructure-types/{infrastructure_type_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/farm-infrastructure-types/{infrastructure_type_id}",
    )

    assert get_response.status_code == 404


def test_delete_farm_infrastructure_type_not_found(client):
    response = client.delete("/api/v1/farm-infrastructure-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm infrastructure type not found."
