def test_create_quality_grade(client):
    response = client.post(
        "/api/v1/quality_grade/",
        json={
            "code": "A",
            "name": "Premium",
            "description": "Highest quality grade",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == "A"
    assert data["name"] == "Premium"


def test_get_quality_grade(client):
    response = client.get("/api/v1/quality_grade/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
