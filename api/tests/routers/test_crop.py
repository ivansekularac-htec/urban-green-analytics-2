def test_create_crop(client):
    response = client.post(
        "/api/v1/crop/",
        json={
            "category_id": 1,
            "name": "Tomato",
            "description": "Red vegetable",
        },
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Tomato"


def test_get_crop(client):
    create = client.post(
        "/api/v1/crop/",
        json={
            "category_id": 1,
            "name": "Cucumber",
            "description": "Green vegetable",
        },
    )
    crop_id = create.json()["id"]

    response = client.get(f"/api/v1/crop/{crop_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Cucumber"
