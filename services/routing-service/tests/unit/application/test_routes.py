import pytest

from routing_service.application.routes import FewestHops, FindCheapestRoute, Leg
from routing_service.domain.errors import DestinationNotFoundError, OriginNotFoundError
from routing_service.domain.graph import Arc, Graph
from routing_service.domain.results import PathResult, TraceStep
from tests.demo_network import demo_graph


class FakeGateway:
    def __init__(self, graph: Graph) -> None:
        self._graph = graph

    def load_graph(self) -> Graph:
        return self._graph


class FakePathFinder:
    """Devuelve el resultado configurado para el par; el caso de uso no depende de Dijkstra."""

    def __init__(self, *results: PathResult) -> None:
        self._results = {(r.origin, r.destination): r for r in results}
        self.calls: list[tuple[str, str, bool]] = []

    def find(
        self, graph: Graph, origin: str, destination: str, *, trace: bool = False
    ) -> PathResult:
        self.calls.append((origin, destination, trace))
        return self._results.get((origin, destination), PathResult(origin, destination, False))


def _found(
    path: tuple[str, ...], legs: tuple[Arc, ...], trace: tuple[TraceStep, ...] = ()
) -> PathResult:
    return PathResult(
        path[0], path[-1], True, path, sum(arc.weight for arc in legs), trace, legs
    )  # fmt: skip


CHEAPEST_NORTE_CENTRO = _found(
    ("B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO"),
    (
        Arc("E02", "B_NORTE", "Z_ALAMEDA", 5),
        Arc("E03", "Z_ALAMEDA", "Z_BOSQUE", 5),
        Arc("E04", "Z_BOSQUE", "Z_CENTRO", 5),
    ),
    (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),),
)
DIRECT_NORTE_CENTRO = _found(("B_NORTE", "Z_CENTRO"), (Arc("E01", "B_NORTE", "Z_CENTRO", 30),))


def _use_case(cheapest: FakePathFinder, fewest: FakePathFinder) -> FindCheapestRoute:
    return FindCheapestRoute(FakeGateway(demo_graph()), cheapest, fewest)


def test_cheaper_path_with_more_hops_than_the_fewest_hops_path() -> None:
    cheapest = FakePathFinder(CHEAPEST_NORTE_CENTRO)
    fewest = FakePathFinder(DIRECT_NORTE_CENTRO)

    report = _use_case(cheapest, fewest).execute("B_NORTE", "Z_CENTRO")

    assert report.found is True
    assert (report.origin, report.destination) == ("B_NORTE", "Z_CENTRO")
    assert report.path == ("B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO")
    assert (report.total_cost, report.hops) == (15.0, 3)
    assert report.legs == (
        Leg("E02", "B_NORTE", "Z_ALAMEDA", 5),
        Leg("E03", "Z_ALAMEDA", "Z_BOSQUE", 5),
        Leg("E04", "Z_BOSQUE", "Z_CENTRO", 5),
    )
    assert report.fewest_hops == FewestHops(("B_NORTE", "Z_CENTRO"), 1, 30.0)
    assert report.message == (
        "Ruta de menor costo: 15 min en 3 tramos (el camino de menos tramos cuesta 30 min)."
    )
    assert report.trace == ()


def test_same_path_for_cost_and_hops_says_so() -> None:
    sur_estacion = _found(
        ("B_SUR", "Z_DELICIAS", "Z_ESTACION"),
        (Arc("E06", "B_SUR", "Z_DELICIAS", 8), Arc("E08", "Z_DELICIAS", "Z_ESTACION", 7)),
    )

    report = _use_case(FakePathFinder(sur_estacion), FakePathFinder(sur_estacion)).execute(
        "B_SUR", "Z_ESTACION"
    )

    assert report.message == (
        "Ruta de menor costo: 15 min en 2 tramos (coincide con el camino de menos tramos)."
    )
    assert report.fewest_hops == FewestHops(sur_estacion.path, 2, 15.0)


def test_a_single_hop_uses_the_singular_and_fractional_minutes_are_kept() -> None:
    direct = _found(("B_OESTE", "Z_FUENTE"), (Arc("E09", "B_OESTE", "Z_FUENTE", 6.5),))

    report = _use_case(FakePathFinder(direct), FakePathFinder(direct)).execute(
        "B_OESTE", "Z_FUENTE"
    )

    assert report.hops == 1
    assert report.message == (
        "Ruta de menor costo: 6.5 min en 1 tramo (coincide con el camino de menos tramos)."
    )


def test_same_origin_and_destination() -> None:
    same = PathResult("B_NORTE", "B_NORTE", True, ("B_NORTE",), 0.0)

    report = _use_case(FakePathFinder(same), FakePathFinder(same)).execute("B_NORTE", "B_NORTE")

    assert report.found is True
    assert report.path == ("B_NORTE",)
    assert (report.total_cost, report.hops, report.legs) == (0.0, 0, ())
    assert report.fewest_hops == FewestHops(("B_NORTE",), 0, 0.0)
    assert report.message == "El origen y el destino son el mismo nodo (B_NORTE): costo 0 min."


def test_no_route_is_not_an_error_and_skips_the_fewest_hops_finder() -> None:
    cheapest = FakePathFinder()
    fewest = FakePathFinder()

    report = _use_case(cheapest, fewest).execute("B_NORTE", "Z_FUENTE")

    assert report.found is False
    assert report.path == ()
    assert (report.total_cost, report.hops, report.fewest_hops) == (None, None, None)
    assert report.legs == ()
    assert report.message == (
        "No hay ruta de B_NORTE a Z_FUENTE: ningún camino de la red los conecta en ese sentido."
    )
    assert cheapest.calls == [("B_NORTE", "Z_FUENTE", False)]
    assert fewest.calls == []


def test_one_way_edge_has_a_route_only_in_one_direction() -> None:
    forward = _found(("B_SUR", "Z_DELICIAS"), (Arc("E06", "B_SUR", "Z_DELICIAS", 8),))
    finder = FakePathFinder(forward)

    use_case = _use_case(finder, FakePathFinder(forward))

    assert use_case.execute("B_SUR", "Z_DELICIAS").found is True
    assert use_case.execute("Z_DELICIAS", "B_SUR").found is False


def test_origin_and_destination_can_be_any_node() -> None:
    zone_to_base = _found(("Z_COLINA", "Z_DELICIAS"), (Arc("E07", "Z_COLINA", "Z_DELICIAS", 12),))

    report = _use_case(FakePathFinder(zone_to_base), FakePathFinder(zone_to_base)).execute(
        "Z_COLINA", "Z_DELICIAS"
    )

    assert report.found is True
    assert report.legs == (Leg("E07", "Z_COLINA", "Z_DELICIAS", 12),)


def test_trace_is_returned_only_when_requested() -> None:
    cheapest = FakePathFinder(CHEAPEST_NORTE_CENTRO)
    fewest = FakePathFinder(DIRECT_NORTE_CENTRO)
    use_case = _use_case(cheapest, fewest)

    with_trace = use_case.execute("B_NORTE", "Z_CENTRO", trace=True)
    without_trace = use_case.execute("B_NORTE", "Z_CENTRO")

    assert with_trace.trace == (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),)
    assert without_trace.trace == ()
    assert cheapest.calls == [("B_NORTE", "Z_CENTRO", True), ("B_NORTE", "Z_CENTRO", False)]
    assert fewest.calls == [("B_NORTE", "Z_CENTRO", False), ("B_NORTE", "Z_CENTRO", False)]


def test_trace_of_a_missing_route_is_kept_when_requested() -> None:
    steps = (TraceStep(1, "pop", "B_NORTE", {"cost": 0.0}),)
    cheapest = FakePathFinder(PathResult("B_NORTE", "Z_FUENTE", False, trace=steps))

    use_case = _use_case(cheapest, FakePathFinder())

    assert use_case.execute("B_NORTE", "Z_FUENTE", trace=True).trace == steps
    assert use_case.execute("B_NORTE", "Z_FUENTE").trace == ()


@pytest.mark.parametrize(
    ("origin", "destination", "error", "code", "node_id", "message"),
    [
        (
            "B_NADA",
            "Z_CENTRO",
            OriginNotFoundError,
            "ORIGIN_NOT_FOUND",
            "B_NADA",
            "El origen 'B_NADA' no existe.",
        ),
        (
            "B_NORTE",
            "Z_NADA",
            DestinationNotFoundError,
            "DESTINATION_NOT_FOUND",
            "Z_NADA",
            "El destino 'Z_NADA' no existe.",
        ),
        (
            "B_NADA",
            "Z_NADA",
            OriginNotFoundError,
            "ORIGIN_NOT_FOUND",
            "B_NADA",
            "El origen 'B_NADA' no existe.",
        ),
    ],
)
def test_unknown_nodes_raise_domain_errors_origin_first(
    origin: str,
    destination: str,
    error: type[Exception],
    code: str,
    node_id: str,
    message: str,
) -> None:
    cheapest = FakePathFinder()
    fewest = FakePathFinder()

    with pytest.raises(error) as raised:
        _use_case(cheapest, fewest).execute(origin, destination)

    assert raised.value.code == code  # type: ignore[attr-defined]
    assert raised.value.message == message  # type: ignore[attr-defined]
    assert raised.value.details == {"node_id": node_id}  # type: ignore[attr-defined]
    assert cheapest.calls == [] and fewest.calls == []


def test_a_found_path_without_cost_violates_the_path_finder_contract() -> None:
    broken = PathResult("B_NORTE", "Z_CENTRO", True, ("B_NORTE", "Z_CENTRO"), None)

    with pytest.raises(RuntimeError, match="PathFinder"):
        _use_case(FakePathFinder(broken), FakePathFinder(DIRECT_NORTE_CENTRO)).execute(
            "B_NORTE", "Z_CENTRO"
        )


def test_a_missing_fewest_hops_path_violates_the_path_finder_contract() -> None:
    with pytest.raises(RuntimeError, match="PathFinder"):
        _use_case(FakePathFinder(CHEAPEST_NORTE_CENTRO), FakePathFinder()).execute(
            "B_NORTE", "Z_CENTRO"
        )
