import copy
from collections.abc import Callable
from typing import Any

import httpx
import pytest

from routing_service.core.errors import AppError
from routing_service.domain.errors import InvalidWeightError
from routing_service.domain.graph import NodeType
from routing_service.infrastructure.network_gateway import HttpNetworkGateway
from tests.demo_network import DEMO_PAYLOAD

API_KEY = "internal-key-for-tests"


def _gateway(handler: Callable[[httpx.Request], httpx.Response]) -> HttpNetworkGateway:
    return HttpNetworkGateway(
        "http://network-service:8001/",
        API_KEY,
        2.0,
        transport=httpx.MockTransport(handler),
    )


def _ok(payload: Any) -> Callable[[httpx.Request], httpx.Response]:
    return lambda _: httpx.Response(200, json=payload)


def _assert_unavailable(gateway: HttpNetworkGateway) -> None:
    with pytest.raises(AppError) as raised:
        gateway.load_graph()
    assert raised.value.code == "NETWORK_UNAVAILABLE"
    assert raised.value.status_code == 503


def test_demo_network_is_converted_to_a_graph() -> None:
    graph = _gateway(_ok(DEMO_PAYLOAD)).load_graph()

    assert len(graph.nodes()) == 11
    assert len(tuple(graph.arcs())) == 8 * 2 + 1  # 8 bidireccionales + 1 de un solo sentido
    assert graph.require_node("B_NORTE").type is NodeType.BASE
    assert len(graph.require_node("B_NORTE").available_technicians) == 1


def test_one_way_edge_has_a_single_arc() -> None:
    graph = _gateway(_ok(DEMO_PAYLOAD)).load_graph()

    assert [a.target for a in graph.neighbors("Z_ESTACION")] == []
    assert "Z_ESTACION" in [a.target for a in graph.neighbors("Z_DELICIAS")]


def test_request_targets_network_with_the_internal_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=DEMO_PAYLOAD)

    _gateway(handler).load_graph()

    assert str(seen[0].url) == "http://network-service:8001/api/v1/network"
    assert seen[0].headers["X-API-Key"] == API_KEY


def test_node_without_technicians_key_is_accepted() -> None:
    payload = {"nodes": [{"id": "Z1", "type": "ZONE", "name": "Uno"}], "edges": []}

    assert _gateway(_ok(payload)).load_graph().has_node("Z1")


@pytest.mark.parametrize("status_code", [401, 403, 404, 500])
def test_error_status_is_unavailable(status_code: int) -> None:
    _assert_unavailable(_gateway(lambda _: httpx.Response(status_code, json={"code": "X"})))


def test_connection_error_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin conexión", request=request)

    _assert_unavailable(_gateway(handler))


def test_timeout_is_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("lento", request=request)

    _assert_unavailable(_gateway(handler))


def test_invalid_json_is_unavailable() -> None:
    _assert_unavailable(_gateway(lambda _: httpx.Response(200, content=b"no es json")))


def test_non_object_json_is_unavailable() -> None:
    _assert_unavailable(_gateway(_ok(["lista"])))


@pytest.mark.parametrize(
    "payload",
    [
        {"nodes": []},
        {"nodes": [{"id": "Z1", "type": "OTRO", "name": "x"}], "edges": []},
        {"nodes": [{"id": "Z1", "type": "ZONE"}], "edges": []},
        {"nodes": [None], "edges": []},
        {"nodes": [], "edges": [{"id": "E1"}]},
    ],
)
def test_payload_that_breaks_the_contract_is_unavailable(payload: dict[str, Any]) -> None:
    _assert_unavailable(_gateway(_ok(payload)))


def test_invalid_weight_is_propagated_as_domain_error() -> None:
    payload = copy.deepcopy(DEMO_PAYLOAD)
    payload["edges"][0]["weight"] = -5

    with pytest.raises(InvalidWeightError):
        _gateway(_ok(payload)).load_graph()
