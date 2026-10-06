from typing import Annotated

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from routing_service.core.errors import register_error_handlers
from routing_service.core.security import Role, require_roles


@pytest.fixture
def query_client() -> TestClient:
    """App mínima con una ruta de consulta (coordinador u operador), como las de Fase 1."""
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/query")
    def query(
        role: Annotated[Role, Depends(require_roles(Role.COORDINATOR, Role.OPERATOR))],
    ) -> dict[str, str]:
        return {"role": role.value}

    return TestClient(app)


@pytest.mark.parametrize(
    ("headers_fixture", "expected_role"),
    [("coordinator_headers", "coordinator"), ("operator_headers", "operator")],
)
def test_allowed_roles_can_query(
    query_client: TestClient,
    request: pytest.FixtureRequest,
    headers_fixture: str,
    expected_role: str,
) -> None:
    response = query_client.get("/query", headers=request.getfixturevalue(headers_fixture))

    assert response.status_code == 200
    assert response.json() == {"role": expected_role}


def test_missing_api_key_is_401(query_client: TestClient) -> None:
    response = query_client.get("/query")

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


def test_invalid_api_key_is_401(query_client: TestClient) -> None:
    response = query_client.get("/query", headers={"X-API-Key": "not-a-real-key-123"})

    assert response.status_code == 401
    assert response.json()["message"] == "API key inválida."


def test_internal_key_cannot_query(
    query_client: TestClient, internal_headers: dict[str, str]
) -> None:
    response = query_client.get("/query", headers=internal_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
