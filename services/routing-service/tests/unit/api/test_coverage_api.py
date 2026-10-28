from collections.abc import Iterator

import httpx
import pytest
from fastapi.testclient import TestClient

from routing_service.api.dependencies import provide_gateway
from routing_service.application.ports import NetworkGateway
from routing_service.infrastructure.network_gateway import HttpNetworkGateway
from routing_service.main import create_app
from tests.demo_network import DEMO_PAYLOAD

URL = "/api/v1/coverage"


def _demo_gateway() -> NetworkGateway:
    return HttpNetworkGateway(
        "http://network-service:8001",
        "internal",
        1.0,
        transport=httpx.MockTransport(lambda _: httpx.Response(200, json=DEMO_PAYLOAD)),
    )


@pytest.fixture
def demo_client() -> Iterator[TestClient]:
    """API real (BFS + gateway real) con network-service simulado por MockTransport."""
    app = create_app()
    app.dependency_overrides[provide_gateway] = _demo_gateway
    with TestClient(app) as test_client:
        yield test_client


def test_coverage_of_demo_base_matches_the_contract(
    demo_client: TestClient, operator_headers: dict[str, str]
) -> None:
    response = demo_client.get(
        URL, params={"base": "B_NORTE", "zone": "Z_CENTRO"}, headers=operator_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["base"] == "B_NORTE"
    assert body["reachable"][:2] == [
        {"node_id": "Z_ALAMEDA", "type": "ZONE", "hops": 1},
        {"node_id": "Z_CENTRO", "type": "ZONE", "hops": 1},
    ]
    assert body["unreachable_zones"] == ["Z_FUENTE", "Z_ISLA"]
    assert body["zone"] == {
        "id": "Z_CENTRO",
        "covered": True,
        "hops": 1,
        "message": "Z_CENTRO está cubierta desde B_NORTE (1 tramo).",
    }
    assert body["trace"] is None


def test_coordinator_can_query_and_zone_is_optional(
    demo_client: TestClient, coordinator_headers: dict[str, str]
) -> None:
    response = demo_client.get(URL, params={"base": "B_NORTE"}, headers=coordinator_headers)

    assert response.status_code == 200
    assert response.json()["zone"] is None


def test_uncovered_zone_answers_200_with_covered_false(
    demo_client: TestClient, operator_headers: dict[str, str]
) -> None:
    response = demo_client.get(
        URL, params={"base": "B_NORTE", "zone": "Z_ISLA"}, headers=operator_headers
    )

    assert response.status_code == 200
    zone = response.json()["zone"]
    assert (zone["covered"], zone["hops"]) == (False, None)
    assert "no hay conexión" in zone["message"]


def test_trace_is_returned_on_demand(
    demo_client: TestClient, operator_headers: dict[str, str]
) -> None:
    response = demo_client.get(
        URL, params={"base": "B_NORTE", "trace": "true"}, headers=operator_headers
    )

    trace = response.json()["trace"]
    assert trace[0] == {"step": 0, "action": "enqueue", "node": "B_NORTE", "data": {"hops": 0}}
    assert len(trace) == 16


@pytest.mark.parametrize(
    ("params", "status_code", "code"),
    [
        ({"base": "B_NADA"}, 404, "ORIGIN_NOT_FOUND"),
        ({"base": "Z_CENTRO"}, 422, "INVALID_ORIGIN"),
        ({"base": "B_NORTE", "zone": "Z_NADA"}, 404, "ZONE_NOT_FOUND"),
    ],
)
def test_domain_errors_use_the_contract_status_and_format(
    demo_client: TestClient,
    operator_headers: dict[str, str],
    params: dict[str, str],
    status_code: int,
    code: str,
) -> None:
    response = demo_client.get(URL, params=params, headers=operator_headers)

    assert response.status_code == status_code
    body = response.json()
    assert body["code"] == code
    assert set(body) == {"code", "message", "details"}
    assert "node_id" in body["details"]


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"base": "b_norte"},
        {"base": "B NORTE"},
        {"base": "B_NORTE", "zone": "z!"},
        {"base": "X" * 33},
    ],
)
def test_invalid_parameters_are_rejected_without_echoing_input(
    demo_client: TestClient, operator_headers: dict[str, str], params: dict[str, str]
) -> None:
    response = demo_client.get(URL, params=params, headers=operator_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert "input" not in response.text


def test_network_unavailable_answers_503(
    operator_headers: dict[str, str],
) -> None:
    def failing_gateway() -> NetworkGateway:
        return HttpNetworkGateway(
            "http://network-service:8001",
            "internal",
            1.0,
            transport=httpx.MockTransport(lambda _: httpx.Response(500)),
        )

    app = create_app()
    app.dependency_overrides[provide_gateway] = failing_gateway
    with TestClient(app) as client:
        response = client.get(URL, params={"base": "B_NORTE"}, headers=operator_headers)

    assert response.status_code == 503
    assert response.json()["code"] == "NETWORK_UNAVAILABLE"


def test_missing_key_is_401(demo_client: TestClient) -> None:
    assert demo_client.get(URL, params={"base": "B_NORTE"}).status_code == 401


def test_internal_role_is_forbidden(
    demo_client: TestClient, internal_headers: dict[str, str]
) -> None:
    response = demo_client.get(URL, params={"base": "B_NORTE"}, headers=internal_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_default_gateway_is_built_from_settings() -> None:
    from routing_service.config import get_settings

    gateway = provide_gateway(get_settings())

    assert isinstance(gateway, HttpNetworkGateway)
