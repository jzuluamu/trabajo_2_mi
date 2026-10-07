from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from network_service.api.dependencies import (
    provide_delete_edge,
    provide_delete_node,
    provide_get_network,
    provide_get_node,
    provide_import_network,
    provide_list_edges,
    provide_list_nodes,
    provide_register_edge,
    provide_register_node,
)
from network_service.domain.errors import (
    DuplicateIdError,
    InvalidWeightError,
    NodeInUseError,
    NodeNotFoundError,
)
from network_service.domain.models import (
    Edge,
    ImportSummary,
    Network,
    Node,
    NodeType,
    Technician,
)
from network_service.main import create_app

PROVIDER_NAMES = {
    provide_register_node: "register_node",
    provide_get_node: "get_node",
    provide_list_nodes: "list_nodes",
    provide_delete_node: "delete_node",
    provide_register_edge: "register_edge",
    provide_list_edges: "list_edges",
    provide_delete_edge: "delete_edge",
    provide_get_network: "get_network",
    provide_import_network: "import_network",
}

NODE_BODY = {
    "id": "B_NORTE",
    "type": "BASE",
    "name": "Base Norte",
    "technicians": [{"id": "T01", "name": "Ana", "available": True}],
}
EDGE_BODY = {
    "id": "E01",
    "source": "B_NORTE",
    "target": "Z_CENTRO",
    "weight": 30,
    "bidirectional": True,
}
NODE = Node(
    id="B_NORTE",
    type=NodeType.BASE,
    name="Base Norte",
    technicians=(Technician(id="T01", name="Ana", available=True),),
)
EDGE = Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=30.0)
NODE_JSON = {
    "id": "B_NORTE",
    "type": "BASE",
    "name": "Base Norte",
    "technicians": [{"id": "T01", "name": "Ana", "available": True}],
}
EDGE_JSON = {
    "id": "E01",
    "source": "B_NORTE",
    "target": "Z_CENTRO",
    "weight": 30.0,
    "bidirectional": True,
}
SEED_IMPORT = {
    "replace": True,
    "nodes": [
        {
            "id": "B_NORTE",
            "type": "BASE",
            "name": "Base Norte",
            "technicians": [
                {"id": "T01", "name": "Ana", "available": True},
                {"id": "T02", "name": "Luis", "available": False},
            ],
        },
        {
            "id": "B_SUR",
            "type": "BASE",
            "name": "Base Sur",
            "technicians": [{"id": "T03", "name": "Marta", "available": True}],
        },
        {
            "id": "B_OESTE",
            "type": "BASE",
            "name": "Base Oeste",
            "technicians": [{"id": "T04", "name": "Pedro", "available": False}],
        },
        {"id": "Z_ALAMEDA", "type": "ZONE", "name": "Alameda"},
        {"id": "Z_BOSQUE", "type": "ZONE", "name": "Bosque"},
        {"id": "Z_CENTRO", "type": "ZONE", "name": "Centro"},
        {"id": "Z_COLINA", "type": "ZONE", "name": "Colina"},
        {"id": "Z_DELICIAS", "type": "ZONE", "name": "Delicias"},
        {"id": "Z_ESTACION", "type": "ZONE", "name": "Estación"},
        {"id": "Z_FUENTE", "type": "ZONE", "name": "Fuente"},
        {"id": "Z_ISLA", "type": "ZONE", "name": "Isla"},
    ],
    "edges": [
        {
            "id": "E01",
            "source": "B_NORTE",
            "target": "Z_CENTRO",
            "weight": 30,
            "bidirectional": True,
        },
        {
            "id": "E02",
            "source": "B_NORTE",
            "target": "Z_ALAMEDA",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E03",
            "source": "Z_ALAMEDA",
            "target": "Z_BOSQUE",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E04",
            "source": "Z_BOSQUE",
            "target": "Z_CENTRO",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E05",
            "source": "Z_CENTRO",
            "target": "Z_COLINA",
            "weight": 10,
            "bidirectional": True,
        },
        {
            "id": "E06",
            "source": "B_SUR",
            "target": "Z_DELICIAS",
            "weight": 8,
            "bidirectional": True,
        },
        {
            "id": "E07",
            "source": "Z_DELICIAS",
            "target": "Z_COLINA",
            "weight": 12,
            "bidirectional": True,
        },
        {
            "id": "E08",
            "source": "Z_DELICIAS",
            "target": "Z_ESTACION",
            "weight": 7,
            "bidirectional": False,
        },
        {
            "id": "E09",
            "source": "B_OESTE",
            "target": "Z_FUENTE",
            "weight": 6,
            "bidirectional": True,
        },
    ],
}


class RecordingUseCase:
    def __init__(self, result: object, error: Exception | None = None) -> None:
        self.result = result
        self.error = error
        self.arguments: tuple[object, ...] | None = None
        self.keyword_arguments: dict[str, object] = {}

    def execute(self, *args: object, **kwargs: object) -> object:
        self.arguments = args
        self.keyword_arguments = kwargs
        if self.error is not None:
            raise self.error
        return self.result


def _use_case_override(use_case: RecordingUseCase) -> Any:
    def override() -> RecordingUseCase:
        return use_case

    return override


@pytest.fixture
def api() -> Iterator[tuple[TestClient, dict[str, RecordingUseCase]]]:
    app = create_app()
    node = NODE
    edge = EDGE
    network = Network(nodes=(node,), edges=(edge,))
    results: dict[str, object] = {
        "register_node": node,
        "get_node": node,
        "list_nodes": [node],
        "delete_node": None,
        "register_edge": edge,
        "list_edges": [edge],
        "delete_edge": None,
        "get_network": network,
        "import_network": ImportSummary(nodes=11, edges=9),
    }
    fakes = {name: RecordingUseCase(result) for name, result in results.items()}
    for provider, name in PROVIDER_NAMES.items():
        app.dependency_overrides[provider] = _use_case_override(fakes[name])
    with TestClient(app) as client:
        yield client, fakes


def _request(
    client: TestClient,
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    return client.request(method.upper(), path, json=body, headers=headers)


def test_post_node_converts_payload_and_returns_created_node(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.post("/api/v1/nodes", json=NODE_BODY, headers=coordinator_headers)

    assert response.status_code == 201
    assert response.json() == NODE_JSON
    assert fakes["register_node"].arguments == (NODE,)


def test_get_nodes_returns_domain_nodes(
    api: tuple[TestClient, dict[str, RecordingUseCase]], operator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.get("/api/v1/nodes", headers=operator_headers)

    assert response.status_code == 200
    assert response.json() == [NODE_JSON]
    assert fakes["list_nodes"].arguments == ()


def test_get_node_passes_unvalidated_path_id(
    api: tuple[TestClient, dict[str, RecordingUseCase]], operator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.get("/api/v1/nodes/not-a-valid-id!", headers=operator_headers)

    assert response.status_code == 200
    assert response.json() == NODE_JSON
    assert fakes["get_node"].arguments == ("not-a-valid-id!",)


def test_delete_node_returns_empty_204_and_passes_id(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.delete("/api/v1/nodes/B_NORTE", headers=coordinator_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert fakes["delete_node"].arguments == ("B_NORTE",)


def test_post_edge_converts_payload_and_returns_created_edge(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.post("/api/v1/edges", json=EDGE_BODY, headers=coordinator_headers)

    assert response.status_code == 201
    assert response.json() == EDGE_JSON
    assert fakes["register_edge"].arguments == (EDGE,)


def test_get_edges_returns_domain_edges(
    api: tuple[TestClient, dict[str, RecordingUseCase]], operator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.get("/api/v1/edges", headers=operator_headers)

    assert response.status_code == 200
    assert response.json() == [EDGE_JSON]
    assert fakes["list_edges"].arguments == ()


def test_delete_edge_returns_empty_204_and_passes_id(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.delete("/api/v1/edges/E01", headers=coordinator_headers)

    assert response.status_code == 204
    assert response.content == b""
    assert fakes["delete_edge"].arguments == ("E01",)


def test_get_network_returns_network_conversion(
    api: tuple[TestClient, dict[str, RecordingUseCase]], internal_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.get("/api/v1/network", headers=internal_headers)

    assert response.status_code == 200
    assert response.json() == {"nodes": [NODE_JSON], "edges": [EDGE_JSON]}
    assert fakes["get_network"].arguments == ()


def test_import_network_converts_seed_payload_and_replace_flag(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api

    response = client.post("/api/v1/network/import", json=SEED_IMPORT, headers=coordinator_headers)

    assert response.status_code == 201
    assert response.json() == {"nodes": 11, "edges": 9}
    fake = fakes["import_network"]
    assert fake.arguments is not None
    imported_nodes, imported_edges = fake.arguments
    assert isinstance(imported_nodes, list)
    assert isinstance(imported_edges, list)
    assert imported_nodes[0] == Node(
        id="B_NORTE",
        type=NodeType.BASE,
        name="Base Norte",
        technicians=(
            Technician(id="T01", name="Ana", available=True),
            Technician(id="T02", name="Luis", available=False),
        ),
    )
    assert imported_edges[0] == Edge(
        id="E01", source="B_NORTE", target="Z_CENTRO", weight=30.0, bidirectional=True
    )
    assert len(imported_nodes) == 11
    assert len(imported_edges) == 9
    assert fake.keyword_arguments == {"replace": True}


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("post", "/api/v1/nodes"),
        ("get", "/api/v1/nodes"),
        ("get", "/api/v1/nodes/B_NORTE"),
        ("delete", "/api/v1/nodes/B_NORTE"),
        ("post", "/api/v1/edges"),
        ("get", "/api/v1/edges"),
        ("delete", "/api/v1/edges/E01"),
        ("get", "/api/v1/network"),
        ("post", "/api/v1/network/import"),
    ],
)
def test_all_routes_require_an_api_key(
    api: tuple[TestClient, dict[str, RecordingUseCase]], method: str, path: str
) -> None:
    client, _ = api

    response = _request(client, method, path)

    assert response.status_code == 401
    assert response.json()["code"] == "UNAUTHENTICATED"


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/v1/nodes", NODE_BODY),
        ("delete", "/api/v1/nodes/B_NORTE", None),
        ("post", "/api/v1/edges", EDGE_BODY),
        ("delete", "/api/v1/edges/E01", None),
        ("post", "/api/v1/network/import", {"nodes": [], "edges": []}),
    ],
)
def test_operator_cannot_write(
    api: tuple[TestClient, dict[str, RecordingUseCase]],
    operator_headers: dict[str, str],
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    client, _ = api

    response = _request(client, method, path, body, operator_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/v1/nodes", NODE_BODY),
        ("get", "/api/v1/nodes", None),
        ("get", "/api/v1/nodes/B_NORTE", None),
        ("delete", "/api/v1/nodes/B_NORTE", None),
        ("post", "/api/v1/edges", EDGE_BODY),
        ("get", "/api/v1/edges", None),
        ("delete", "/api/v1/edges/E01", None),
        ("post", "/api/v1/network/import", {"nodes": [], "edges": []}),
    ],
)
def test_internal_role_can_only_read_complete_network(
    api: tuple[TestClient, dict[str, RecordingUseCase]],
    internal_headers: dict[str, str],
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    client, _ = api

    response = _request(client, method, path, body, internal_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.parametrize(
    "body",
    [
        {"id": "CLIENT_SECRET", "type": "BASE"},
        {**NODE_BODY, "extra": "CLIENT_SECRET"},
        {**NODE_BODY, "type": "INVALID_TYPE"},
    ],
)
def test_node_shape_errors_are_422_without_reflecting_input(
    api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
    body: dict[str, object],
) -> None:
    client, _ = api

    response = client.post("/api/v1/nodes", json=body, headers=coordinator_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "CLIENT_SECRET" not in response.text


def test_non_numeric_weight_is_validation_error_without_reflection(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, _ = api

    response = client.post(
        "/api/v1/edges",
        json={**EDGE_BODY, "weight": "CLIENT_SECRET"},
        headers=coordinator_headers,
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "CLIENT_SECRET" not in response.text


def test_negative_weight_reaches_use_case_and_domain_error_is_mapped(
    api: tuple[TestClient, dict[str, RecordingUseCase]], coordinator_headers: dict[str, str]
) -> None:
    client, fakes = api
    fakes["register_edge"].error = InvalidWeightError(
        "El peso debe estar entre 0 y 1440.", edge_id="E01"
    )

    response = client.post(
        "/api/v1/edges",
        json={**EDGE_BODY, "weight": -1},
        headers=coordinator_headers,
    )

    assert response.status_code == 422
    assert response.json() == {
        "code": "INVALID_WEIGHT",
        "message": "El peso debe estar entre 0 y 1440.",
        "details": {"edge_id": "E01"},
    }
    assert fakes["register_edge"].arguments == (
        Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=-1.0),
    )


@pytest.mark.parametrize(
    ("provider_name", "method", "path", "body", "error", "expected"),
    [
        (
            "get_node",
            "get",
            "/api/v1/nodes/MISSING",
            None,
            NodeNotFoundError("El nodo 'MISSING' no existe.", node_id="MISSING"),
            {
                "code": "NODE_NOT_FOUND",
                "message": "El nodo 'MISSING' no existe.",
                "details": {"node_id": "MISSING"},
            },
        ),
        (
            "register_node",
            "post",
            "/api/v1/nodes",
            NODE_BODY,
            DuplicateIdError("Ya existe el nodo.", node_id="B_NORTE"),
            {
                "code": "DUPLICATE_ID",
                "message": "Ya existe el nodo.",
                "details": {"node_id": "B_NORTE"},
            },
        ),
        (
            "delete_node",
            "delete",
            "/api/v1/nodes/B_NORTE",
            None,
            NodeInUseError("El nodo tiene conexiones.", node_id="B_NORTE", edge_ids=["E01"]),
            {
                "code": "NODE_IN_USE",
                "message": "El nodo tiene conexiones.",
                "details": {"node_id": "B_NORTE", "edge_ids": ["E01"]},
            },
        ),
    ],
)
def test_domain_errors_keep_contract_status_and_shape(
    api: tuple[TestClient, dict[str, RecordingUseCase]],
    coordinator_headers: dict[str, str],
    operator_headers: dict[str, str],
    provider_name: str,
    method: str,
    path: str,
    body: dict[str, object] | None,
    error: Exception,
    expected: dict[str, object],
) -> None:
    client, fakes = api
    fakes[provider_name].error = error
    headers = operator_headers if method == "get" else coordinator_headers

    response = _request(client, method, path, body, headers)

    assert response.status_code in (404, 409, 422)
    assert response.json() == expected


def test_openapi_contains_all_nine_f1c_routes(
    api: tuple[TestClient, dict[str, RecordingUseCase]],
) -> None:
    client, _ = api

    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert {
        "/api/v1/nodes",
        "/api/v1/nodes/{node_id}",
        "/api/v1/edges",
        "/api/v1/edges/{edge_id}",
        "/api/v1/network",
        "/api/v1/network/import",
    } <= paths.keys()
    assert set(paths["/api/v1/nodes"]) == {"get", "post"}
    assert set(paths["/api/v1/nodes/{node_id}"]) == {"get", "delete"}
    assert set(paths["/api/v1/edges"]) == {"get", "post"}
    assert set(paths["/api/v1/edges/{edge_id}"]) == {"delete"}
    assert set(paths["/api/v1/network"]) == {"get"}
    assert set(paths["/api/v1/network/import"]) == {"post"}
