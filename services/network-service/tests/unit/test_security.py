from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from network_service.core.errors import register_error_handlers
from network_service.core.security import Role, require_roles


@pytest.mark.parametrize(
    ("headers_fixture", "expected_role"),
    [
        ("coordinator_headers", "coordinator"),
        ("operator_headers", "operator"),
        ("internal_headers", "internal"),
    ],
)
def test_whoami_returns_role_for_each_valid_key(
    client: TestClient, request: pytest.FixtureRequest, headers_fixture: str, expected_role: str
) -> None:
    headers = request.getfixturevalue(headers_fixture)

    response = client.get("/api/v1/auth/whoami", headers=headers)

    assert response.status_code == 200
    assert response.json() == {"role": expected_role}


def test_missing_api_key_is_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/whoami")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_invalid_api_key_is_401(client: TestClient) -> None:
    response = client.get("/api/v1/auth/whoami", headers={"X-API-Key": "not-a-real-key-123"})

    assert response.status_code == 401
    assert response.json() == {
        "code": "UNAUTHENTICATED",
        "message": "API key inválida.",
        "details": {},
    }


def _app_with_coordinator_only_route() -> FastAPI:
    app = FastAPI()
    register_error_handlers(app)

    @app.post("/write")
    def write(role: Annotated[Role, Depends(require_roles(Role.COORDINATOR))]) -> dict[str, str]:
        return {"role": role.value}

    return app


def test_operator_cannot_use_coordinator_route(operator_headers: dict[str, str]) -> None:
    client = TestClient(_app_with_coordinator_only_route())

    response = client.post("/write", headers=operator_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_coordinator_can_use_coordinator_route(coordinator_headers: dict[str, str]) -> None:
    client = TestClient(_app_with_coordinator_only_route())

    response = client.post("/write", headers=coordinator_headers)

    assert response.status_code == 200
    assert response.json() == {"role": "coordinator"}
