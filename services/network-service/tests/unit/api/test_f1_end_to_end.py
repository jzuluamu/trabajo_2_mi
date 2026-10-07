"""Prueba punta a punta de F1 por HTTP (carril F1-D).

Usa `create_app()` con los proveedores REALES (casos de uso y reglas) y solo reemplaza
`get_repository` por un `InMemoryNetworkRepository` nuevo por prueba. La persistencia en
PostgreSQL la cubren `tests/integration/` y `scripts/smoke_f1.sh`.

`tests/fixtures/red_demo.json` es una copia de `seed/red_demo.json`: la imagen de pruebas solo
ve la carpeta del servicio. `make smoke-f1` importa el archivo original contra Docker.
"""

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from network_service.api.dependencies import get_repository
from network_service.infrastructure.memory_repository import InMemoryNetworkRepository
from network_service.main import create_app

DEMO = json.loads((Path(__file__).parents[2] / "fixtures" / "red_demo.json").read_text("utf-8"))

ZONE = {"id": "Z_NUEVA", "type": "ZONE", "name": "Nueva"}
BASE = {
    "id": "B_ESTE",
    "type": "BASE",
    "name": "Base Este",
    "technicians": [{"id": "T10", "name": "Sara", "available": True}],
}
EDGE = {"id": "E10", "source": "B_ESTE", "target": "Z_NUEVA", "weight": 12, "bidirectional": True}


@pytest.fixture
def api() -> Iterator[TestClient]:
    app = create_app()
    repository = InMemoryNetworkRepository()
    app.dependency_overrides[get_repository] = lambda: repository
    with TestClient(app) as client:
        yield client


@pytest.fixture
def demo_api(api: TestClient, coordinator_headers: dict[str, str]) -> TestClient:
    response = api.post("/api/v1/network/import", json=DEMO, headers=coordinator_headers)
    assert response.status_code == 201
    return api


def _error(response: Any) -> tuple[int, str]:
    return response.status_code, response.json()["code"]


# --- red demo -------------------------------------------------------------------------


def test_import_demo_network_and_read_it_sorted(
    api: TestClient, coordinator_headers: dict[str, str], operator_headers: dict[str, str]
) -> None:
    imported = api.post("/api/v1/network/import", json=DEMO, headers=coordinator_headers)
    network = api.get("/api/v1/network", headers=operator_headers).json()

    assert (imported.status_code, imported.json()) == (201, {"nodes": 11, "edges": 9})
    node_ids = [node["id"] for node in network["nodes"]]
    edge_ids = [edge["id"] for edge in network["edges"]]
    assert (len(node_ids), len(edge_ids)) == (11, 9)
    assert node_ids == sorted(node_ids)
    assert edge_ids == sorted(edge_ids)
    assert network["nodes"][0] == DEMO["nodes"][0]  # B_NORTE con sus técnicos
    assert {"id": "E08", "bidirectional": False}.items() <= network["edges"][7].items()


def test_internal_role_reads_the_network(
    demo_api: TestClient, internal_headers: dict[str, str]
) -> None:
    response = demo_api.get("/api/v1/network", headers=internal_headers)

    assert response.status_code == 200
    assert len(response.json()["nodes"]) == 11


def test_import_replace_true_discards_previous_network(
    demo_api: TestClient, coordinator_headers: dict[str, str]
) -> None:
    payload = {"nodes": [ZONE], "edges": [], "replace": True}

    response = demo_api.post("/api/v1/network/import", json=payload, headers=coordinator_headers)
    network = demo_api.get("/api/v1/network", headers=coordinator_headers).json()

    assert response.status_code == 201
    assert network == {"nodes": [ZONE | {"technicians": []}], "edges": []}


# --- ciclo completo -------------------------------------------------------------------


def test_full_cycle_create_list_get_and_delete(
    api: TestClient, coordinator_headers: dict[str, str], operator_headers: dict[str, str]
) -> None:
    assert api.post("/api/v1/nodes", json=BASE, headers=coordinator_headers).status_code == 201
    assert api.post("/api/v1/nodes", json=ZONE, headers=coordinator_headers).status_code == 201
    created_edge = api.post("/api/v1/edges", json=EDGE, headers=coordinator_headers)

    assert created_edge.status_code == 201
    assert created_edge.json() == EDGE | {"weight": 12.0}
    assert [n["id"] for n in api.get("/api/v1/nodes", headers=operator_headers).json()] == [
        "B_ESTE",
        "Z_NUEVA",
    ]
    assert api.get("/api/v1/nodes/B_ESTE", headers=operator_headers).json() == BASE
    assert [e["id"] for e in api.get("/api/v1/edges", headers=operator_headers).json()] == ["E10"]

    assert api.delete("/api/v1/edges/E10", headers=coordinator_headers).status_code == 204
    assert api.delete("/api/v1/nodes/B_ESTE", headers=coordinator_headers).status_code == 204
    assert api.delete("/api/v1/nodes/Z_NUEVA", headers=coordinator_headers).status_code == 204
    assert api.get("/api/v1/network", headers=operator_headers).json() == {
        "nodes": [],
        "edges": [],
    }


# --- errores del contrato -------------------------------------------------------------


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        ({**ZONE, "id": "z_minuscula"}, (422, "VALIDATION_ERROR")),
        ({**ZONE, "technicians": BASE["technicians"]}, (422, "VALIDATION_ERROR")),
        ({**ZONE, "type": "CASA"}, (422, "VALIDATION_ERROR")),
        ({**ZONE, "id": "Z_CENTRO"}, (409, "DUPLICATE_ID")),
        ({**BASE, "technicians": [{"id": "T01", "name": "Otra"}]}, (409, "DUPLICATE_ID")),
    ],
)
def test_node_errors_through_http(
    demo_api: TestClient,
    coordinator_headers: dict[str, str],
    body: dict[str, Any],
    expected: tuple[int, str],
) -> None:
    response = demo_api.post("/api/v1/nodes", json=body, headers=coordinator_headers)

    assert _error(response) == expected


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        ({"weight": -5}, (422, "INVALID_WEIGHT")),
        ({"weight": 0}, (422, "INVALID_WEIGHT")),
        ({"weight": 1441}, (422, "INVALID_WEIGHT")),
        ({"weight": True}, (422, "VALIDATION_ERROR")),
        ({"weight": "30"}, (422, "VALIDATION_ERROR")),
        ({"target": "Z_ISLA", "source": "Z_ISLA"}, (422, "SELF_LOOP")),
        ({"id": "E01"}, (409, "DUPLICATE_ID")),
        ({"target": "Z_NO_EXISTE"}, (404, "NODE_NOT_FOUND")),
        ({"source": "Z_CENTRO", "target": "B_NORTE"}, (409, "DUPLICATE_EDGE")),
    ],
)
def test_edge_errors_through_http(
    demo_api: TestClient,
    coordinator_headers: dict[str, str],
    changes: dict[str, Any],
    expected: tuple[int, str],
) -> None:
    body = {"id": "E10", "source": "Z_ISLA", "target": "Z_FUENTE", "weight": 4} | changes

    response = demo_api.post("/api/v1/edges", json=body, headers=coordinator_headers)

    assert _error(response) == expected


def test_invalid_weight_message_is_readable(
    demo_api: TestClient, coordinator_headers: dict[str, str]
) -> None:
    body = {"id": "E10", "source": "Z_ISLA", "target": "Z_FUENTE", "weight": -5}

    response = demo_api.post("/api/v1/edges", json=body, headers=coordinator_headers)

    assert response.json() == {
        "code": "INVALID_WEIGHT",
        "message": "El peso de la conexión 'E10' debe ser mayor que 0 y menor o igual a "
        "1440 minutos.",
        "details": {"edge_id": "E10"},
    }


def test_delete_errors_through_http(
    demo_api: TestClient, coordinator_headers: dict[str, str]
) -> None:
    in_use = demo_api.delete("/api/v1/nodes/Z_CENTRO", headers=coordinator_headers)
    missing_node = demo_api.delete("/api/v1/nodes/Z_NO_EXISTE", headers=coordinator_headers)
    missing_edge = demo_api.delete("/api/v1/edges/E99", headers=coordinator_headers)

    assert _error(in_use) == (409, "NODE_IN_USE")
    assert in_use.json()["details"]["edge_ids"] == ["E01", "E04", "E05"]
    assert _error(missing_node) == (404, "NODE_NOT_FOUND")
    assert _error(missing_edge) == (404, "EDGE_NOT_FOUND")


def test_malformed_path_id_is_not_reflected(
    demo_api: TestClient, operator_headers: dict[str, str]
) -> None:
    response = demo_api.get("/api/v1/nodes/%3Cscript%3E", headers=operator_headers)

    assert _error(response) == (404, "NODE_NOT_FOUND")
    assert "<script>" not in response.text


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("POST", "/api/v1/nodes", ZONE),
        ("POST", "/api/v1/edges", EDGE),
        ("DELETE", "/api/v1/nodes/Z_ISLA", None),
        ("DELETE", "/api/v1/edges/E01", None),
        ("POST", "/api/v1/network/import", DEMO),
    ],
)
def test_operator_cannot_write(
    demo_api: TestClient,
    operator_headers: dict[str, str],
    method: str,
    path: str,
    body: dict[str, Any] | None,
) -> None:
    response = demo_api.request(method, path, json=body, headers=operator_headers)

    assert _error(response) == (403, "FORBIDDEN")


@pytest.mark.parametrize("path", ["/api/v1/network", "/api/v1/nodes", "/api/v1/edges"])
def test_missing_api_key_is_unauthenticated(demo_api: TestClient, path: str) -> None:
    assert _error(demo_api.get(path)) == (401, "UNAUTHENTICATED")


# --- importación atómica --------------------------------------------------------------


def test_import_with_an_invalid_edge_saves_nothing(
    demo_api: TestClient, coordinator_headers: dict[str, str]
) -> None:
    payload = {
        "nodes": [ZONE],
        "edges": [
            {"id": "E10", "source": "Z_NUEVA", "target": "Z_ISLA", "weight": 3},
            {"id": "E11", "source": "Z_NUEVA", "target": "Z_FUENTE", "weight": -1},
        ],
    }
    before = demo_api.get("/api/v1/network", headers=coordinator_headers).json()

    response = demo_api.post("/api/v1/network/import", json=payload, headers=coordinator_headers)

    assert _error(response) == (422, "INVALID_WEIGHT")
    assert response.json()["details"] == {"edge_id": "E11", "section": "edges", "index": 1}
    assert demo_api.get("/api/v1/network", headers=coordinator_headers).json() == before
