"""
Harvest API tests.
"""

from uuid import uuid4


def create_crop_category(client) -> int:
    """Create a crop category test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": f"Harvest Category Dependency {suffix}",
            "description": "Harvest category dependency",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_crop(client) -> int:
    """Create a crop test dependency."""
    suffix = uuid4().hex[:8]
    category_id = create_crop_category(client)

    response = client.post(
        "/api/v1/crops",
        json={
            "name": f"Harvest Crop Dependency {suffix}",
            "description": "Harvest crop dependency",
            "category_id": category_id,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_farm(client) -> int:
    """Create a farm test dependency."""
    suffix = uuid4().hex[:8]

    infrastructure_response = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": f"Harvest Infrastructure {suffix}",
            "description": "Harvest infrastructure dependency",
        },
    )

    growing_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"Harvest Growing System {suffix}",
            "description": "Harvest growing system dependency",
        },
    )

    assert infrastructure_response.status_code == 201
    assert growing_response.status_code == 201

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_response.json()["id"],
            "growing_system_type_id": growing_response.json()["id"],
            "name": f"Harvest Farm Dependency {suffix}",
            "city": "Belgrade",
            "size_m2": 800,
            "growing_beds_count": 8,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_quality_grade(client) -> int:
    """Create a quality grade test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": f"HQG_{suffix}",
            "name": f"Harvest Quality Grade {suffix}",
            "description": "Harvest quality grade dependency",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_harvest_crud(client):
    """Test harvest CRUD endpoints."""
    farm_id = create_farm(client)
    crop_id = create_crop(client)
    quality_grade_id = create_quality_grade(client)

    create_response = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm_id,
            "crop_id": crop_id,
            "quality_grade_id": quality_grade_id,
            "weight_kg": 120.5,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    harvest_id = created["id"]

    list_response = client.get("/api/v1/harvests")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/harvests/{harvest_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == harvest_id

    update_response = client.put(
        f"/api/v1/harvests/{harvest_id}",
        json={"weight_kg": 150.75},
    )

    assert update_response.status_code == 200

    delete_response = client.delete(f"/api/v1/harvests/{harvest_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/harvests/{harvest_id}")
    assert missing_response.status_code == 404
