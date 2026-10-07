from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from network_service.api.dependencies import (
    provide_delete_edge,
    provide_list_edges,
    provide_register_edge,
)
from network_service.domain.errors import InvalidWeightError
from network_service.domain.models import Edge
from network_service.main import create_app

EDGE = Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=30.0)
EDGE_BODY = {
    "id": "E01",
    "source": "B_NORTE",
    "target": "Z_CENTRO",
    "weight": 30,
    "bidirectional": True,
}
EDGE_JSON = {**EDGE_BODY, "weight": 30.0}


class RecordingUseCase:
    def __init__(self, result: object) -> None:
        self.result = result
        self.error: Exception | None = None
        self.arguments: tuple[object, ...] | None = None

    def execute(self, *args: object, **kwargs: object) -> object:
        self.arguments = args
        if self.error is not None:
            raise self.error
        return self.result


@pytest.fixture
def edge_api() -> Iterator[tuple[TestClient, dict[str, RecordingUseCase]]]:
    app = create_app()
    fakes = {
        "register": RecordingUseCase(EDGE),
        "list": RecordingUseCase([EDGE]),
        "delete": RecordingUseCase(None),
    }
    app.dependency_overrides[provide_register_edge] = lambda: fakes["register"]
    app.dependency_overrides[provide_list_edges] = lambda: fakes["list"]
    app.dependency_overrides[provide_delete_edge] = lambda: fakes["delete"]
    with TestClient(app) as client:
        yield client, fakes


def test_register_edge_returns_created_edge_and_passes_domain_entity(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = edge_api

    response = client.post("/api/v1/edges", json=EDGE_BODY, headers=coordinator_headers)

    assert response.status_code == 201
    assert response.json() == EDGE_JSON
    assert fakes["register"].arguments == (EDGE,)


def test_list_edges_returns_list(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]], operator_headers: dict[str, str]
) -> None:
    client, fakes = edge_api

    response = client.get("/api/v1/edges", headers=operator_headers)

    assert response.status_code == 200
    assert response.json() == [EDGE_JSON]
    assert fakes["list"].arguments == ()


def test_delete_edge_returns_empty_204(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = edge_api

    response = client.delete("/api/v1/edges/E01", headers=coordinator_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert fakes["delete"].arguments == ("E01",)


def test_negative_weight_is_not_rejected_by_schema(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = edge_api
    fakes["register"].error = InvalidWeightError(
        "El peso debe estar entre 0 y 1440.", edge_id="E01"
    )

    response = client.post(
        "/api/v1/edges",
        json={**EDGE_BODY, "weight": -1},
        headers=coordinator_headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_WEIGHT"
    assert fakes["register"].arguments == (
        Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=-1.0),
    )


@pytest.mark.parametrize(
    "body",
    [
        {**EDGE_BODY, "weight": "DO_NOT_ECHO"},
        {**EDGE_BODY, "unexpected": "DO_NOT_ECHO"},
    ],
)
def test_invalid_edge_payload_is_not_reflected(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
    body: dict[str, Any],
) -> None:
    client, _ = edge_api

    response = client.post("/api/v1/edges", json=body, headers=coordinator_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "DO_NOT_ECHO" not in response.text


@pytest.mark.parametrize("weight", [True, "30"])
def test_weight_must_be_a_json_number(
    edge_api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
    weight: object,
) -> None:
    client, fakes = edge_api

    response = client.post(
        "/api/v1/edges", json={**EDGE_BODY, "weight": weight}, headers=coordinator_headers
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert fakes["register"].arguments is None
