import pytest

from routing_service.application.attention import (
    AlternativeBase,
    AvailableTechnician,
    BestBase,
    FindBestAttention,
)
from routing_service.domain.errors import ZoneNotFoundError
from routing_service.domain.graph import Graph, Node, NodeType, Technician
from routing_service.domain.results import PathResult, TraceStep
from tests.demo_network import demo_graph


class FakeGateway:
    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    def load_graph(self) -> Graph:
        return self._graph


class FakePathFinder:
    """Devuelve el `PathResult` configurado para cada par (base, zona)."""

    def __init__(self, *results: PathResult) -> None:
        self._results = {(r.origin, r.destination): r for r in results}
        self.calls: list[tuple[str, str, bool]] = []

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        self.calls.append((origin, destination, trace))
        return self._results.get((origin, destination), PathResult(origin, destination, False))


def _found(path: tuple[str, ...], cost: float, trace: tuple[TraceStep, ...] = ()) -> PathResult:
    return PathResult(path[0], path[-1], True, path, cost, trace)


# Resultados de la red demo (docs/05): los que Dijkstra real devolvería desde cada base.
NORTE_COLINA = _found(("B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO", "Z_COLINA"), 25.0)
SUR_COLINA = _found(("B_SUR", "Z_DELICIAS", "Z_COLINA"), 20.0)
SUR_ESTACION = _found(("B_SUR", "Z_DELICIAS", "Z_ESTACION"), 15.0)
NORTE_ESTACION = _found(
    ("B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO", "Z_COLINA", "Z_DELICIAS", "Z_ESTACION"),
    44.0,
)
OESTE_FUENTE = _found(("B_OESTE", "Z_FUENTE"), 6.0)


def _use_case(finder: FakePathFinder, graph: Graph | None = None) -> FindBestAttention:
    return FindBestAttention(FakeGateway(graph or demo_graph()), finder)


def test_colina_is_attended_from_the_cheapest_base_with_the_other_as_alternative() -> None:
    report = _use_case(FakePathFinder(NORTE_COLINA, SUR_COLINA)).execute("Z_COLINA")

    assert report.zone == "Z_COLINA"
    assert report.found is True
    assert report.best == BestBase(
        "B_SUR", (AvailableTechnician("T03", "Marta"),), SUR_COLINA.path, 20.0, 2
    )
    assert report.alternatives == (AlternativeBase("B_NORTE", 25.0, 4),)
    assert report.message == "Atender desde B_SUR (Marta): 20 min."
    assert report.trace == ()


def test_estacion_is_attended_from_b_sur_with_a_far_alternative() -> None:
    report = _use_case(FakePathFinder(NORTE_ESTACION, SUR_ESTACION)).execute("Z_ESTACION")

    assert report.best is not None
    assert (report.best.base, report.best.total_cost, report.best.hops) == ("B_SUR", 15.0, 2)
    assert report.alternatives == (AlternativeBase("B_NORTE", 44.0, 6),)
    assert report.message == "Atender desde B_SUR (Marta): 15 min."


def test_fuente_is_only_reachable_from_a_base_without_available_technicians() -> None:
    finder = FakePathFinder(OESTE_FUENTE)

    report = _use_case(finder).execute("Z_FUENTE")

    assert report.found is False
    assert report.best is None
    assert report.alternatives == ()
    assert report.message == (
        "Z_FUENTE no se puede atender: solo es alcanzable desde bases sin técnicos "
        "disponibles (B_OESTE)."
    )
    assert finder.calls == [
        ("B_NORTE", "Z_FUENTE", False),
        ("B_SUR", "Z_FUENTE", False),
        ("B_OESTE", "Z_FUENTE", False),
    ]


def test_isla_is_unreachable_from_every_base() -> None:
    finder = FakePathFinder()

    report = _use_case(finder).execute("Z_ISLA")

    assert report.found is False
    assert report.best is None
    assert report.alternatives == ()
    assert report.message == "Z_ISLA no se puede atender: es inalcanzable desde toda base."
    assert [call[0] for call in finder.calls] == ["B_NORTE", "B_SUR", "B_OESTE"]


def test_a_base_without_available_technicians_is_never_a_candidate() -> None:
    finder = FakePathFinder(OESTE_FUENTE, _found(("B_NORTE", "Z_FUENTE"), 99.0))

    report = _use_case(finder).execute("Z_FUENTE")

    assert report.best is not None
    assert report.best.base == "B_NORTE"
    assert report.alternatives == ()
    assert ("B_OESTE", "Z_FUENTE", False) not in finder.calls


def test_best_lists_only_the_available_technicians() -> None:
    report = _use_case(FakePathFinder(NORTE_COLINA)).execute("Z_COLINA")

    assert report.best is not None
    assert report.best.technicians == (AvailableTechnician("T01", "Ana"),)
    assert report.message == "Atender desde B_NORTE (Ana): 25 min."


def test_several_available_technicians_are_joined_in_the_message() -> None:
    graph = Graph()
    graph.add_node(
        Node(
            "B_A",
            NodeType.BASE,
            "Base A",
            (
                Technician("T1", "Ana", True),
                Technician("T2", "Luis", False),
                Technician("T3", "Eva", True),
            ),
        )
    )
    graph.add_node(Node("Z_X", NodeType.ZONE, "X"))

    report = _use_case(FakePathFinder(_found(("B_A", "Z_X"), 7.5)), graph).execute("Z_X")

    assert report.best is not None
    assert report.best.technicians == (
        AvailableTechnician("T1", "Ana"),
        AvailableTechnician("T3", "Eva"),
    )
    assert report.message == "Atender desde B_A (Ana, Eva): 7.5 min."


def test_tie_on_cost_is_broken_by_fewer_hops() -> None:
    norte = _found(("B_NORTE", "Z_A", "Z_B", "Z_COLINA"), 20.0)
    sur = _found(("B_SUR", "Z_A", "Z_COLINA"), 20.0)

    report = _use_case(FakePathFinder(norte, sur)).execute("Z_COLINA")

    assert report.best is not None and report.best.base == "B_SUR"
    assert report.alternatives == (AlternativeBase("B_NORTE", 20.0, 3),)


def test_tie_on_cost_and_hops_is_broken_by_base_id() -> None:
    norte = _found(("B_NORTE", "Z_A", "Z_COLINA"), 20.0)
    sur = _found(("B_SUR", "Z_A", "Z_COLINA"), 20.0)

    report = _use_case(FakePathFinder(sur, norte)).execute("Z_COLINA")

    assert report.best is not None and report.best.base == "B_NORTE"
    assert report.alternatives == (AlternativeBase("B_SUR", 20.0, 2),)


def test_a_cheaper_base_wins_even_with_more_hops() -> None:
    norte = _found(("B_NORTE", "Z_A", "Z_B", "Z_C", "Z_COLINA"), 18.0)
    sur = _found(("B_SUR", "Z_COLINA"), 19.0)

    report = _use_case(FakePathFinder(norte, sur)).execute("Z_COLINA")

    assert report.best is not None and report.best.base == "B_NORTE"


def test_trace_concatenates_each_candidate_in_id_order_tagged_with_its_base() -> None:
    norte = _found(NORTE_COLINA.path, 25.0, (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),))
    sur = _found(
        SUR_COLINA.path,
        20.0,
        (
            TraceStep(1, "pop", "B_SUR", {"cost": 0.0}),
            TraceStep(1, "relax", "Z_DELICIAS", {"cost": 8.0, "from": "B_SUR", "edge_id": "E06"}),
        ),
    )
    finder = FakePathFinder(sur, norte)

    report = _use_case(finder).execute("Z_COLINA", trace=True)

    assert report.trace == (
        TraceStep(1, "pop", "B_NORTE", {"cost": 0.0, "base": "B_NORTE"}),
        TraceStep(1, "pop", "B_SUR", {"cost": 0.0, "base": "B_SUR"}),
        TraceStep(
            1,
            "relax",
            "Z_DELICIAS",
            {"cost": 8.0, "from": "B_SUR", "edge_id": "E06", "base": "B_SUR"},
        ),
    )
    assert finder.calls == [("B_NORTE", "Z_COLINA", True), ("B_SUR", "Z_COLINA", True)]
    # los pasos originales del buscador no se modifican
    assert norte.trace[0].data == {"cost": 0.0}


def test_trace_includes_candidates_that_do_not_reach_the_zone() -> None:
    unreachable = PathResult(
        "B_NORTE", "Z_FUENTE", False, trace=(TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),)
    )

    report = _use_case(FakePathFinder(unreachable)).execute("Z_FUENTE", trace=True)

    assert report.found is False
    assert report.trace == (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0, "base": "B_NORTE"}),)


def test_trace_is_empty_unless_requested_even_if_the_finder_returns_steps() -> None:
    steps = (TraceStep(1, "pop", "B_SUR", {"cost": 0.0}),)
    finder = FakePathFinder(_found(SUR_COLINA.path, 20.0, steps))

    report = _use_case(finder).execute("Z_COLINA")

    assert report.trace == ()
    assert finder.calls[-1] == ("B_SUR", "Z_COLINA", False)


@pytest.mark.parametrize("zone", ["Z_NADA", "B_SUR"])
def test_unknown_zone_or_base_passed_as_zone_raises_zone_not_found(zone: str) -> None:
    finder = FakePathFinder()

    with pytest.raises(ZoneNotFoundError) as raised:
        _use_case(finder).execute(zone)

    assert raised.value.code == "ZONE_NOT_FOUND"
    assert raised.value.message == f"La zona '{zone}' no existe."
    assert raised.value.details == {"node_id": zone}
    assert finder.calls == []


def test_a_found_path_without_cost_violates_the_path_finder_contract() -> None:
    broken = PathResult("B_SUR", "Z_COLINA", True, ("B_SUR", "Z_COLINA"), None)

    with pytest.raises(RuntimeError, match="PathFinder"):
        _use_case(FakePathFinder(broken)).execute("Z_COLINA")
