"""
test_farm_crops.py
Tests for farm crop CRUD endpoints.
"""


def create_infrastructure_type(client) -> int:
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Hydroponic",
            "description": "Infrastructure",
        },
    )

    return response.json()["id"]


def create_growing_system_type(client) -> int:
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Tower",
            "description": "Growing system",
        },
    )

    return response.json()["id"]


def create_farm(client) -> int:
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": "Test Farm",
            "city": "Belgrade",
            "size_m2": "120.500",
            "status": "ACTIVE",
            "growing_beds_count": 10,
        },
    )

    return response.json()["id"]


def create_crop_category(client) -> int:
    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Herbs",
            "description": "Herbs category",
        },
    )

    return response.json()["id"]


def create_crop(client) -> int:
    category_id = create_crop_category(client)

    response = client.post(
        "/api/v1/crops",
        json={
            "category_id": category_id,
            "name": "Basil",
            "description": "Fresh basil",
        },
    )

    return response.json()["id"]


def create_farm_crop_payload(
    farm_id: int,
    crop_id: int,
) -> dict[str, object]:
    return {
        "farm_id": farm_id,
        "crop_id": crop_id,
        "started_at": 1710000000,
        "ended_at": None,
    }


def test_create_farm_crop(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            crop_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == farm_id
    assert data["crop_id"] == crop_id
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_farm_crop_invalid_input(client):
    response = client.post(
        "/api/v1/farm-crops",
        json={},
    )

    assert response.status_code == 422


def test_create_farm_crop_with_missing_farm(client):
    crop_id = create_crop(client)

    response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            999,
            crop_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_create_farm_crop_with_missing_crop(client):
    farm_id = create_farm(client)

    response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found."


def test_get_farm_crops(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            crop_id,
        ),
    )

    response = client.get("/api/v1/farm-crops")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_farm_crop(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    create_response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            crop_id,
        ),
    )

    farm_crop_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/farm-crops/{farm_crop_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == farm_crop_id
    assert data["farm_id"] == farm_id
    assert data["crop_id"] == crop_id


def test_get_farm_crop_not_found(client):
    response = client.get("/api/v1/farm-crops/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm crop not found."


def test_update_farm_crop(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    create_response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            crop_id,
        ),
    )

    farm_crop_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/farm-crops/{farm_crop_id}",
        json={
            "started_at": 1720000000,
            "ended_at": 1730000000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == farm_crop_id
    assert data["farm_id"] == farm_id
    assert data["crop_id"] == crop_id
    assert data["started_at"] == 1720000000
    assert data["ended_at"] == 1730000000


def test_update_farm_crop_not_found(client):
    response = client.put(
        "/api/v1/farm-crops/999",
        json={
            "crop_id": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm crop not found."


def test_delete_farm_crop(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    create_response = client.post(
        "/api/v1/farm-crops",
        json=create_farm_crop_payload(
            farm_id,
            crop_id,
        ),
    )

    farm_crop_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/farm-crops/{farm_crop_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/farm-crops/{farm_crop_id}",
    )

    assert get_response.status_code == 404


def test_delete_farm_crop_not_found(client):
    response = client.delete("/api/v1/farm-crops/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm crop not found."
