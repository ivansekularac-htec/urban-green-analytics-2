"""
test_farms.py
Tests for farm CRUD endpoints.
"""


def create_infrastructure_type(client) -> int:
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Hydroponic",
            "description": "Water-based growing infrastructure",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_growing_system_type(client) -> int:
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Tower",
            "description": "Vertical tower growing system",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_farm_payload(
    infrastructure_type_id: int,
    growing_system_type_id: int,
) -> dict:
    return {
        "infrastructure_type_id": infrastructure_type_id,
        "growing_system_type_id": growing_system_type_id,
        "name": "Test Farm",
        "city": "Belgrade",
        "size_m2": "120.500",
        "status": "ACTIVE",
        "growing_beds_count": 20,
    }


def test_create_farm(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["infrastructure_type_id"] == infrastructure_type_id
    assert data["growing_system_type_id"] == growing_system_type_id
    assert data["name"] == "Test Farm"
    assert data["city"] == "Belgrade"
    assert data["size_m2"] == "120.500" or float(data["size_m2"]) == 120.5
    assert data["status"] == "ACTIVE"
    assert data["growing_beds_count"] == 20
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_farm_invalid_input(client):
    response = client.post(
        "/api/v1/farms",
        json={
            "name": "Invalid Farm",
        },
    )

    assert response.status_code == 422


def test_create_farm_with_missing_infrastructure_type(client):
    growing_system_type_id = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            999,
            growing_system_type_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm infrastructure type not found."


def test_create_farm_with_missing_growing_system_type(client):
    infrastructure_type_id = create_infrastructure_type(client)

    response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found."


def test_get_farms(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    response = client.get("/api/v1/farms")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Test Farm"
    assert data[0]["city"] == "Belgrade"


def test_get_farm(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.get(f"/api/v1/farms/{farm_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == farm_id
    assert data["name"] == "Test Farm"
    assert data["infrastructure_type_id"] == infrastructure_type_id
    assert data["growing_system_type_id"] == growing_system_type_id


def test_get_farm_not_found(client):
    response = client.get("/api/v1/farms/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_update_farm(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": "Updated Farm",
            "city": "Novi Sad",
            "size_m2": "250.000",
            "status": "MAINTENANCE",
            "growing_beds_count": 50,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == farm_id
    assert data["name"] == "Updated Farm"
    assert data["city"] == "Novi Sad"
    assert data["status"] == "MAINTENANCE"
    assert data["growing_beds_count"] == 50


def test_update_farm_partial(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={
            "city": "Pancevo",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Test Farm"
    assert data["city"] == "Pancevo"
    assert data["status"] == "ACTIVE"


def test_update_farm_not_found(client):
    response = client.put(
        "/api/v1/farms/999",
        json={
            "name": "Missing Farm",
            "city": "Belgrade",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_update_farm_with_missing_infrastructure_type(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={
            "infrastructure_type_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm infrastructure type not found."


def test_update_farm_with_missing_growing_system_type(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={
            "growing_system_type_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found."


def test_delete_farm(client):
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json=create_farm_payload(
            infrastructure_type_id,
            growing_system_type_id,
        ),
    )

    farm_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/farms/{farm_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/farms/{farm_id}")

    assert get_response.status_code == 404


def test_delete_farm_not_found(client):
    response = client.delete("/api/v1/farms/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."
