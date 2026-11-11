from collections.abc import Iterator
from contextlib import contextmanager

from fastapi.testclient import TestClient

from routing_service.api.dependencies import provide_find_best_attention
from routing_service.application.attention import (
    AlternativeBase,
    AttentionReport,
    AvailableTechnician,
    BestBase,
)
from routing_service.core.errors import AppError
from routing_service.domain.errors import InvalidWeightError, ZoneNotFoundError
from routing_service.domain.results import TraceStep
from routing_service.main import create_app

URL = "/api/v1/attention/best"


class FakeAttentionUseCase:
    def __init__(
        self, report: AttentionReport | None = None, error: Exception | None = None
    ) -> None:
        self.report = report
        self.error = error
        self.calls: list[tuple[str, bool]] = []

    def execute(self, zone: str, *, trace: bool = False) -> AttentionReport:
        self.calls.append((zone, trace))
        if self.error is not None:
            raise self.error
        if self.report is None:
            raise AssertionError("Falta el reporte falso de atención.")
        return self.report


@contextmanager
def _client(use_case: FakeAttentionUseCase) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[provide_find_best_attention] = lambda: use_case
    with TestClient(app) as client:
        yield client


def _report(*, found: bool = True, trace: tuple[TraceStep, ...] = ()) -> AttentionReport:
    if not found:
        return AttentionReport(
            zone="Z_ISLA",
            found=False,
            best=None,
            alternatives=(),
            message="Z_ISLA no se puede atender: es inalcanzable desde toda base.",
            trace=trace,
        )
    return AttentionReport(
        zone="Z_COLINA",
        found=True,
        best=BestBase(
            "B_SUR",
            (AvailableTechnician("T03", "Marta"),),
            ("B_SUR", "Z_COLINA"),
            20.0,
            2,
        ),
        alternatives=(AlternativeBase("B_NORTE", 25.0, 4),),
        message="Atender desde B_SUR (Marta): 20 min.",
        trace=trace,
    )


def test_complete_attention_response_has_best_and_alternatives(
    operator_headers: dict[str, str],
) -> None:
    use_case = FakeAttentionUseCase(_report())
    with _client(use_case) as client:
        response = client.get(URL, params={"zone": "Z_COLINA"}, headers=operator_headers)

    assert response.status_code == 200
    assert response.json() == {
        "zone": "Z_COLINA",
        "found": True,
        "best": {
            "base": "B_SUR",
            "technicians": [{"id": "T03", "name": "Marta"}],
            "path": ["B_SUR", "Z_COLINA"],
            "total_cost": 20.0,
            "hops": 2,
        },
        "alternatives": [{"base": "B_NORTE", "total_cost": 25.0, "hops": 4}],
        "message": "Atender desde B_SUR (Marta): 20 min.",
        "trace": None,
    }
    assert use_case.calls == [("Z_COLINA", False)]


def test_unavailable_zone_answers_200_with_found_false(
    operator_headers: dict[str, str],
) -> None:
    with _client(FakeAttentionUseCase(_report(found=False))) as client:
        response = client.get(URL, params={"zone": "Z_ISLA"}, headers=operator_headers)

    body = response.json()
    assert response.status_code == 200
    assert (body["found"], body["best"], body["alternatives"]) == (False, None, [])
    assert body["trace"] is None


def test_trace_is_returned_only_when_requested(operator_headers: dict[str, str]) -> None:
    steps = (TraceStep(1, "pop", "B_SUR", {"cost": 0.0, "base": "B_SUR"}),)
    use_case = FakeAttentionUseCase(_report(trace=steps))
    with _client(use_case) as client:
        response = client.get(
            URL, params={"zone": "Z_COLINA", "trace": "true"}, headers=operator_headers
        )

    assert response.status_code == 200
    assert response.json()["trace"] == [
        {
            "step": 1,
            "action": "pop",
            "node": "B_SUR",
            "data": {"cost": 0.0, "base": "B_SUR"},
        }
    ]
    assert use_case.calls == [("Z_COLINA", True)]


def test_missing_zone_is_404(operator_headers: dict[str, str]) -> None:
    error = ZoneNotFoundError("La zona no existe.", node_id="Z_MISSING")
    with _client(FakeAttentionUseCase(error=error)) as client:
        response = client.get(URL, params={"zone": "Z_MISSING"}, headers=operator_headers)

    assert response.status_code == 404
    assert response.json()["code"] == "ZONE_NOT_FOUND"


def test_invalid_weight_is_422(operator_headers: dict[str, str]) -> None:
    error = InvalidWeightError("Peso inválido.", edge_id="E_BAD")
    with _client(FakeAttentionUseCase(error=error)) as client:
        response = client.get(URL, params={"zone": "Z_COLINA"}, headers=operator_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "INVALID_WEIGHT"


def test_invalid_zone_id_answers_422_without_echoing_input(
    operator_headers: dict[str, str],
) -> None:
    invalid_id = "secret<script>"
    with _client(FakeAttentionUseCase(_report())) as client:
        response = client.get(URL, params={"zone": invalid_id}, headers=operator_headers)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"
    assert invalid_id not in response.text
    assert "input" not in response.text


def test_network_unavailable_is_503(operator_headers: dict[str, str]) -> None:
    error = AppError("NETWORK_UNAVAILABLE", "No se pudo obtener la red.", 503)
    with _client(FakeAttentionUseCase(error=error)) as client:
        response = client.get(URL, params={"zone": "Z_COLINA"}, headers=operator_headers)

    assert response.status_code == 503
    assert response.json()["code"] == "NETWORK_UNAVAILABLE"


def test_missing_key_is_401() -> None:
    with _client(FakeAttentionUseCase(_report())) as client:
        response = client.get(URL, params={"zone": "Z_COLINA"})

    assert response.status_code == 401


def test_internal_role_is_forbidden(internal_headers: dict[str, str]) -> None:
    with _client(FakeAttentionUseCase(_report())) as client:
        response = client.get(URL, params={"zone": "Z_COLINA"}, headers=internal_headers)

    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"
