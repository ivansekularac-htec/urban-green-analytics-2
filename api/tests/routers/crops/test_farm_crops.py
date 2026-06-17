"""
Farm crop API tests.
"""

from uuid import uuid4


def create_crop_category(client) -> int:
    """Create a crop category test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": f"Farm Crop Category Dependency {suffix}",
            "description": "Farm crop category dependency",
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
            "name": f"Farm Crop Dependency Crop {suffix}",
            "description": "Farm crop dependency crop",
            "category_id": category_id,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_farm_dependencies(client) -> tuple[int, int]:
    """Create farm lookup test dependencies."""
    suffix = uuid4().hex[:8]

    infrastructure_response = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": f"Farm Crop Infrastructure {suffix}",
            "description": "Farm crop infrastructure dependency",
        },
    )

    growing_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"Farm Crop Growing System {suffix}",
            "description": "Farm crop growing system dependency",
        },
    )

    assert infrastructure_response.status_code == 201
    assert growing_response.status_code == 201

    return infrastructure_response.json()["id"], growing_response.json()["id"]


def create_farm(client) -> int:
    """Create a farm test dependency."""
    suffix = uuid4().hex[:8]
    infrastructure_type_id, growing_system_type_id = create_farm_dependencies(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": f"Farm Crop Dependency Farm {suffix}",
            "city": "Belgrade",
            "size_m2": 1000,
            "growing_beds_count": 10,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_farm_crop_crud(client):
    """Test farm crop CRUD endpoints."""
    farm_id = create_farm(client)
    crop_id = create_crop(client)

    create_response = client.post(
        "/api/v1/farm-crops",
        json={
            "farm_id": farm_id,
            "crop_id": crop_id,
            "started_at": 1_700_000_000,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    farm_crop_id = created["id"]

    list_response = client.get("/api/v1/farm-crops")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/farm-crops/{farm_crop_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == farm_crop_id

    update_response = client.put(
        f"/api/v1/farm-crops/{farm_crop_id}",
        json={"ended_at": 1_700_086_400},
    )

    assert update_response.status_code == 200
    assert update_response.json()["ended_at"] == 1_700_086_400

    delete_response = client.delete(f"/api/v1/farm-crops/{farm_crop_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/farm-crops/{farm_crop_id}")
    assert missing_response.status_code == 404
