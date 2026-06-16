"""
Quality grade API tests.
"""

from uuid import uuid4


def test_quality_grade_crud(client):
    """Test quality grade CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": f"QG_{suffix}",
            "name": f"Test Quality Grade {suffix}",
            "description": "Test quality grade description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    quality_grade_id = created["id"]

    list_response = client.get("/api/v1/quality-grades")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/quality-grades/{quality_grade_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == quality_grade_id

    update_response = client.put(
        f"/api/v1/quality-grades/{quality_grade_id}",
        json={"name": f"Updated Quality Grade {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Quality Grade {suffix}"

    delete_response = client.delete(f"/api/v1/quality-grades/{quality_grade_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/quality-grades/{quality_grade_id}")
    assert missing_response.status_code == 404
