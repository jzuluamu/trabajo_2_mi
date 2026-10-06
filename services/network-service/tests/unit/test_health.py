from fastapi.testclient import TestClient


def test_health_is_public_and_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "network-service"}


def test_openapi_documents_the_api(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/v1/auth/whoami" in response.json()["paths"]
