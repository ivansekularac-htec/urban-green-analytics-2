def test_create_crop_category(client):
    response = client.post(
        "/api/v1/crop_category/",
        json={"name": "Vegetables", "description": "All vegetable crops"},
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Vegetables"
    assert "id" in data


def test_get_crop_category(client):
    response = client.get("/api/v1/crop_category/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
