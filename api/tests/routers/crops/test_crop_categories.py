"""
Crop category API tests.
"""

from uuid import uuid4


def test_crop_category_crud(client):
    """Test crop category CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": f"Test Crop Category {suffix}",
            "description": "Test crop category description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    crop_category_id = created["id"]

    list_response = client.get("/api/v1/crop-categories")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/crop-categories/{crop_category_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == crop_category_id

    update_response = client.put(
        f"/api/v1/crop-categories/{crop_category_id}",
        json={"name": f"Updated Crop Category {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Crop Category {suffix}"

    delete_response = client.delete(f"/api/v1/crop-categories/{crop_category_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/crop-categories/{crop_category_id}")
    assert missing_response.status_code == 404
