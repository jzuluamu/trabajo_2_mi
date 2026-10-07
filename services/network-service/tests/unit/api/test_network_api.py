from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from network_service.api.dependencies import provide_get_network, provide_import_network
from network_service.domain.models import ImportSummary, Network, Node, NodeType
from network_service.main import create_app


class RecordingUseCase:
    def __init__(self, result: object) -> None:
        self.result = result
        self.arguments: tuple[object, ...] | None = None
        self.keyword_arguments: dict[str, object] = {}

    def execute(self, *args: object, **kwargs: object) -> object:
        self.arguments = args
        self.keyword_arguments = kwargs
        return self.result


@pytest.fixture
def network_api() -> Iterator[tuple[TestClient, dict[str, RecordingUseCase]]]:
    app = create_app()
    fakes = {
        "get": RecordingUseCase(Network(nodes=(), edges=())),
        "import": RecordingUseCase(ImportSummary(nodes=0, edges=0)),
    }
    app.dependency_overrides[provide_get_network] = lambda: fakes["get"]
    app.dependency_overrides[provide_import_network] = lambda: fakes["import"]
    with TestClient(app) as client:
        yield client, fakes


def test_get_network_is_available_to_internal_role(
    network_api: tuple[TestClient, dict[str, RecordingUseCase]], internal_headers: dict[str, str]
) -> None:
    client, fakes = network_api

    response = client.get("/api/v1/network", headers=internal_headers)

    assert response.status_code == 200
    assert response.json() == {"nodes": [], "edges": []}
    assert fakes["get"].arguments == ()


def test_import_network_passes_domain_lists_and_replace(
    network_api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
) -> None:
    client, fakes = network_api
    payload = {
        "nodes": [{"id": "B_NORTE", "type": "BASE", "name": "Base Norte"}],
        "edges": [],
        "replace": True,
    }

    response = client.post("/api/v1/network/import", json=payload, headers=coordinator_headers)

    assert response.status_code == 201
    assert response.json() == {"nodes": 0, "edges": 0}
    assert fakes["import"].arguments == (
        [Node(id="B_NORTE", type=NodeType.BASE, name="Base Norte")],
        [],
    )
    assert fakes["import"].keyword_arguments == {"replace": True}


def test_import_defaults_replace_to_false(
    network_api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
) -> None:
    client, fakes = network_api

    response = client.post(
        "/api/v1/network/import",
        json={"nodes": [], "edges": []},
        headers=coordinator_headers,
    )

    assert response.status_code == 201
    assert fakes["import"].keyword_arguments == {"replace": False}


def test_network_endpoints_are_documented_in_openapi(
    network_api: tuple[TestClient, dict[str, RecordingUseCase]],
) -> None:
    client, _ = network_api

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert set(paths["/api/v1/network"]) == {"get"}
    assert set(paths["/api/v1/network/import"]) == {"post"}
