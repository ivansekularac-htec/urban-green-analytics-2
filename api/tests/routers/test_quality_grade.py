def test_get_quality_grades(client):
    response = client.get("/api/v1/quality-grades/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_quality_grade(client):
    response = client.post(
        "/api/v1/quality-grades/",
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


def test_create_quality_grade_invalid_payload(client):
    response = client.post(
        "/api/v1/quality-grades/",
        json={},
    )

    assert response.status_code == 422


def test_update_quality_grade_not_found(client):
    response = client.put(
        "/api/v1/quality-grades/999999",
        json={
            "name": "Updated Grade",
        },
    )

    assert response.status_code == 404
