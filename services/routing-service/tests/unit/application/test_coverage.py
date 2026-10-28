import pytest

from routing_service.application.coverage import (
    CheckCoverage,
    CoverageReport,
    ReachableNode,
)
from routing_service.domain.coverage.bfs import BreadthFirstReachability
from routing_service.domain.errors import (
    DomainError,
    InvalidOriginError,
    OriginNotFoundError,
    ZoneNotFoundError,
)
from routing_service.domain.graph import Graph, NodeType
from routing_service.domain.results import ReachabilityResult, TraceStep
from tests.demo_network import demo_graph


class FakeGateway:
    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    def load_graph(self) -> Graph:
        return self._graph


class FakeStrategy:
    """Devuelve un resultado fijo; el caso de uso no debe depender del BFS real."""

    def __init__(self, hops: dict[str, int]) -> None:
        self._hops = hops
        self.calls: list[tuple[str, bool]] = []

    def reachable_from(
        self, graph: Graph, origin: str, *, trace: bool = False
    ) -> ReachabilityResult:
        self.calls.append((origin, trace))
        return ReachabilityResult(origin, self._hops, (TraceStep(0, "enqueue", origin),))


def _use_case(hops: dict[str, int]) -> tuple[CheckCoverage, FakeStrategy]:
    strategy = FakeStrategy(hops)
    return CheckCoverage(FakeGateway(demo_graph()), strategy), strategy


def test_reachable_excludes_origin_and_is_sorted_by_hops_then_id() -> None:
    use_case, _ = _use_case({"B_NORTE": 0, "Z_CENTRO": 1, "Z_ALAMEDA": 1, "Z_BOSQUE": 2})

    report = use_case.execute("B_NORTE")

    assert report.reachable == (
        ReachableNode("Z_ALAMEDA", NodeType.ZONE, 1),
        ReachableNode("Z_CENTRO", NodeType.ZONE, 1),
        ReachableNode("Z_BOSQUE", NodeType.ZONE, 2),
    )


def test_unreachable_zones_exclude_bases_and_are_sorted() -> None:
    use_case, _ = _use_case({"B_NORTE": 0, "Z_CENTRO": 1})

    report = use_case.execute("B_NORTE")

    assert report.unreachable_zones == (
        "Z_ALAMEDA",
        "Z_BOSQUE",
        "Z_COLINA",
        "Z_DELICIAS",
        "Z_ESTACION",
        "Z_FUENTE",
        "Z_ISLA",
    )


def test_without_zone_the_zone_section_is_none() -> None:
    use_case, _ = _use_case({"B_NORTE": 0})

    assert use_case.execute("B_NORTE").zone is None


def test_covered_zone_reports_hops_and_singular_message() -> None:
    use_case, _ = _use_case({"B_NORTE": 0, "Z_CENTRO": 1})

    zone = use_case.execute("B_NORTE", "Z_CENTRO").zone

    assert zone is not None
    assert (zone.id, zone.covered, zone.hops) == ("Z_CENTRO", True, 1)
    assert zone.message == "Z_CENTRO está cubierta desde B_NORTE (1 tramo)."


def test_covered_zone_message_uses_plural() -> None:
    use_case, _ = _use_case({"B_NORTE": 0, "Z_COLINA": 3})

    zone = use_case.execute("B_NORTE", "Z_COLINA").zone

    assert zone is not None
    assert zone.message == "Z_COLINA está cubierta desde B_NORTE (3 tramos)."


def test_uncovered_zone_is_not_an_error() -> None:
    use_case, _ = _use_case({"B_NORTE": 0})

    zone = use_case.execute("B_NORTE", "Z_ISLA").zone

    assert zone is not None
    assert (zone.covered, zone.hops) == (False, None)
    assert "no hay conexión" in zone.message


def test_trace_is_forwarded_only_when_requested() -> None:
    use_case, strategy = _use_case({"B_NORTE": 0})

    with_trace = use_case.execute("B_NORTE", trace=True)
    without_trace = use_case.execute("B_NORTE")

    assert with_trace.trace == (TraceStep(0, "enqueue", "B_NORTE"),)
    assert without_trace.trace == ()
    assert strategy.calls == [("B_NORTE", True), ("B_NORTE", False)]


@pytest.mark.parametrize(
    ("base", "zone", "error", "code"),
    [
        ("B_NADA", None, OriginNotFoundError, "ORIGIN_NOT_FOUND"),
        ("Z_CENTRO", None, InvalidOriginError, "INVALID_ORIGIN"),
        ("B_NORTE", "Z_NADA", ZoneNotFoundError, "ZONE_NOT_FOUND"),
        ("B_NORTE", "B_SUR", ZoneNotFoundError, "ZONE_NOT_FOUND"),
    ],
)
def test_invalid_queries_raise_domain_errors(
    base: str, zone: str | None, error: type[DomainError], code: str
) -> None:
    use_case, strategy = _use_case({})

    with pytest.raises(error) as raised:
        use_case.execute(base, zone)

    assert raised.value.code == code
    assert raised.value.details == {"node_id": zone or base}
    assert strategy.calls == []


def test_origin_is_validated_before_the_zone() -> None:
    use_case, _ = _use_case({})

    with pytest.raises(OriginNotFoundError):
        use_case.execute("B_NADA", "Z_NADA")


def test_real_bfs_on_the_demo_network() -> None:
    use_case = CheckCoverage(FakeGateway(demo_graph()), BreadthFirstReachability())

    report: CoverageReport = use_case.execute("B_NORTE", "Z_FUENTE")

    assert report.unreachable_zones == ("Z_FUENTE", "Z_ISLA")
    assert [(n.node_id, n.hops) for n in report.reachable][:2] == [
        ("Z_ALAMEDA", 1),
        ("Z_CENTRO", 1),
    ]
    assert report.zone is not None and not report.zone.covered
