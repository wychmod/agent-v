from fastapi.testclient import TestClient


def test_status_routes(client: TestClient):
    response = client.get("/api/status")
    data = response.json()
    assert response.status_code == 200
    assert data["code"] == 200
