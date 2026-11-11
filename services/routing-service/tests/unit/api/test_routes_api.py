from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from fastapi.testclient import TestClient

from routing_service.api.dependencies import (
    provide_fewest_hops_finder,
    provide_find_best_attention,
    provide_find_cheapest_route,
    provide_gateway,
    provide_path_finder,
)
from routing_service.application.attention import FindBestAttention
from routing_service.application.ports import NetworkGateway
from routing_service.application.routes import FewestHops, FindCheapestRoute, Leg, RouteReport
from routing_service.config import get_settings
from routing_service.core.errors import AppError
from routing_service.domain.cheapest_path.dijkstra import DijkstraPathFinder
from routing_service.domain.cheapest_path.fewest_hops import BreadthFirstPathFinder
from routing_service.domain.errors import (
    DestinationNotFoundError,
    DomainError,
    InvalidWeightError,
    OriginNotFoundError,
)
from routing_service.domain.results import TraceStep
from routing_service.main import create_app

URL = "/api/v1/routes/cheapest"


class FakeRouteUseCase:
    def __init__(self, report: RouteReport | None = None, error: Exception | None = None) -> None:
        self.report = report
        self.error = error
        self.calls: list[tuple[str, str, bool]] = []

    def execute(self, origin: str, destination: str, *, trace: bool = False) -> RouteReport:
        self.calls.append((origin, destination, trace))
        if self.error is not None:
            raise self.error
        if self.report is None:
            raise AssertionError("Falta el reporte falso de ruta.")
        return self.report


@contextmanager
def _client(use_case: FakeRouteUseCase) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[provide_find_cheapest_route] = lambda: use_case
    with TestClient(app) as client:
        yield client


def _report(*, found: bool = True, trace: tuple[TraceStep, ...] = ()) -> RouteReport:
    if not found:
        return RouteReport(
            found=False,
            origin="B_NORTE",
            destination="Z_FUENTE",
            path=(),
            total_cost=None,
            hops=None,
            legs=(),
            fewest_hops=None,
            message="No hay ruta de B_NORTE a Z_FUENTE.",
            trace=trace,
        )
    return RouteReport(
        found=True,
        origin="B_NORTE",
        destination="Z_CENTRO",
        path=("B_NORTE", "Z_CENTRO"),
        total_cost=5.0,
        hops=1,
        legs=(Leg("E01", "B_NORTE", "Z_CENTRO", 5.0),),
        fewest_hops=FewestHops(("B_NORTE", "Z_CENTRO"), 1, 5.0),
        message="Ruta de menor costo: 5 min en 1 tramo.",
        trace=trace,
    )


def test_complete_route_response_uses_from_to_and_null_trace_by_default(
    operator_headers: dict[str, str],
) -> None:
    use_case = FakeRouteUseCase(_report())
    with _client(use_case) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 200
    assert response.json() == {
        "found": True,
        "origin": "B_NORTE",
        "destination": "Z_CENTRO",
        "path": ["B_NORTE", "Z_CENTRO"],
        "total_cost": 5.0,
        "hops": 1,
        "legs": [{"edge_id": "E01", "from": "B_NORTE", "to": "Z_CENTRO", "weight": 5.0}],
        "fewest_hops": {"path": ["B_NORTE", "Z_CENTRO"], "hops": 1, "cost": 5.0},
        "message": "Ruta de menor costo: 5 min en 1 tramo.",
        "trace": None,
    }
    assert use_case.calls == [("B_NORTE", "Z_CENTRO", False)]


def test_unreachable_route_answers_200_with_found_false(
    operator_headers: dict[str, str],
) -> None:
    with _client(FakeRouteUseCase(_report(found=False))) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_FUENTE"},
            headers=operator_headers,
        )

    body = response.json()
    assert response.status_code == 200
    assert (body["found"], body["path"], body["legs"], body["fewest_hops"]) == (False, [], [], None)
    assert (body["total_cost"], body["hops"], body["trace"]) == (None, None, None)


def test_trace_is_returned_only_when_requested(operator_headers: dict[str, str]) -> None:
    steps = (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),)
    use_case = FakeRouteUseCase(_report(trace=steps))
    with _client(use_case) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO", "trace": "true"},
            headers=operator_headers,
        )

    assert response.status_code == 200
    assert response.json()["trace"] == [
        {"step": 1, "action": "pop", "node": "B_NORTE", "data": {"cost": 0.0}}
    ]
    assert use_case.calls == [("B_NORTE", "Z_CENTRO", True)]


@pytest.mark.parametrize(
    ("error", "code"),
    [
        (OriginNotFoundError("Origen inexistente.", node_id="B_MISSING"), "ORIGIN_NOT_FOUND"),
        (
            DestinationNotFoundError("Destino inexistente.", node_id="Z_MISSING"),
            "DESTINATION_NOT_FOUND",
        ),
    ],
)
def test_missing_origin_or_destination_is_404(
    operator_headers: dict[str, str], error: DomainError, code: str
) -> None:
    with _client(FakeRouteUseCase(error=error)) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 404
    assert response.json()["code"] == code


def test_invalid_weight_is_422(operator_headers: dict[str, str]) -> None:
    error = InvalidWeightError("Peso inválido.", edge_id="E_BAD")
    with _client(FakeRouteUseCase(error=error)) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_WEIGHT"


class UnknownDomainError(DomainError):
    code = "UNMAPPED_ERROR"


def test_unmapped_domain_error_uses_400(operator_headers: dict[str, str]) -> None:
    with _client(FakeRouteUseCase(error=UnknownDomainError("Error de dominio."))) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 400
    assert response.json()["code"] == "UNMAPPED_ERROR"


def test_invalid_id_answers_422_without_echoing_input(
    operator_headers: dict[str, str],
) -> None:
    invalid_id = "secret<script>"
    with _client(FakeRouteUseCase(_report())) as client:
        response = client.get(
            URL,
            params={"origin": invalid_id, "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert invalid_id not in response.text
    assert "input" not in response.text


def test_network_unavailable_is_503(operator_headers: dict[str, str]) -> None:
    error = AppError("NETWORK_UNAVAILABLE", "No se pudo obtener la red.", 503)
    with _client(FakeRouteUseCase(error=error)) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=operator_headers,
        )

    assert response.status_code == 503
    assert response.json()["code"] == "NETWORK_UNAVAILABLE"


def test_missing_key_is_401() -> None:
    with _client(FakeRouteUseCase(_report())) as client:
        response = client.get(URL, params={"origin": "B_NORTE", "destination": "Z_CENTRO"})

    assert response.status_code == 401


def test_internal_role_is_forbidden(internal_headers: dict[str, str]) -> None:
    with _client(FakeRouteUseCase(_report())) as client:
        response = client.get(
            URL,
            params={"origin": "B_NORTE", "destination": "Z_CENTRO"},
            headers=internal_headers,
        )

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


def test_providers_build_route_use_cases_and_finders() -> None:
    gateway: NetworkGateway = provide_gateway(get_settings())
    path_finder = provide_path_finder()
    fewest_hops_finder = provide_fewest_hops_finder()

    assert isinstance(path_finder, DijkstraPathFinder)
    assert isinstance(fewest_hops_finder, BreadthFirstPathFinder)
    assert isinstance(
        provide_find_cheapest_route(gateway, path_finder, fewest_hops_finder),
        FindCheapestRoute,
    )
    assert isinstance(provide_find_best_attention(gateway, path_finder), FindBestAttention)
