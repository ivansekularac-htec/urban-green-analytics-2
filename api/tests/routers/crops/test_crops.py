"""
Crop API tests.
"""

from uuid import uuid4


def create_crop_category(client) -> int:
    """Create a crop category test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": f"Crop Dependency Category {suffix}",
            "description": "Crop dependency category",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_crop_crud(client):
    """Test crop CRUD endpoints."""
    suffix = uuid4().hex[:8]
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json={
            "name": f"Test Crop {suffix}",
            "description": "Test crop description",
            "category_id": category_id,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    crop_id = created["id"]

    list_response = client.get("/api/v1/crops")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/crops/{crop_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == crop_id

    update_response = client.put(
        f"/api/v1/crops/{crop_id}",
        json={"name": f"Updated Crop {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Crop {suffix}"

    delete_response = client.delete(f"/api/v1/crops/{crop_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/crops/{crop_id}")
    assert missing_response.status_code == 404
