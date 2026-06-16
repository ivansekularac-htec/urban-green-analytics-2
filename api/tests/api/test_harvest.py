"""
test_harvests.py
Tests for harvest CRUD endpoints.
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


def create_quality_grade(client) -> int:
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Grade A",
            "description": "Premium quality",
        },
    )

    return response.json()["id"]


def create_harvest_payload(
    farm_id: int,
    crop_id: int,
    quality_grade_id: int,
) -> dict[str, object]:
    return {
        "farm_id": farm_id,
        "crop_id": crop_id,
        "quality_grade_id": quality_grade_id,
        "weight_kg": "125.500",
    }


def test_create_harvest(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            quality_grade_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == farm_id
    assert data["crop_id"] == crop_id
    assert data["quality_grade_id"] == quality_grade_id
    assert float(data["weight_kg"]) == 125.5


def test_create_harvest_invalid_input(client):
    response = client.post(
        "/api/v1/harvests",
        json={},
    )

    assert response.status_code == 422


def test_create_harvest_missing_farm(client):
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            999,
            crop_id,
            quality_grade_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_create_harvest_missing_crop(client):
    farm_id = create_farm(client)
    quality_grade_id = create_quality_grade(client)

    response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            999,
            quality_grade_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found."


def test_create_harvest_missing_quality_grade(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found."


def test_get_harvests(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            quality_grade_id,
        ),
    )

    response = client.get("/api/v1/harvests")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_harvest_not_found(client):
    response = client.get("/api/v1/harvests/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Harvest not found."


def test_update_harvest(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    create_response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            quality_grade_id,
        ),
    )

    harvest_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/harvests/{harvest_id}",
        json={
            "weight_kg": "200.000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == harvest_id
    assert float(data["weight_kg"]) == 200.0


def test_update_harvest_not_found(client):
    response = client.put(
        "/api/v1/harvests/999",
        json={
            "weight_kg": "200.000",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Harvest not found."


def test_delete_harvest(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    create_response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            quality_grade_id,
        ),
    )

    harvest_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/harvests/{harvest_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/harvests/{harvest_id}",
    )

    assert get_response.status_code == 404


def test_delete_harvest_not_found(client):
    response = client.delete("/api/v1/harvests/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Harvest not found."


def test_update_harvest_with_missing_quality_grade(client):
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    create_response = client.post(
        "/api/v1/harvests",
        json=create_harvest_payload(
            farm_id,
            crop_id,
            quality_grade_id,
        ),
    )

    harvest_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/harvests/{harvest_id}",
        json={
            "quality_grade_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found."
