"""Caso de uso de ruta de menor costo — IMPLEMENTA: carril F3-B (docs/features/F3-sesiones.md).

Los dataclasses, la clase, el constructor y la firma de `execute` están CONGELADOS (base de F3):
el carril F3-C (API) los importa. F3-B reemplaza solo el cuerpo de `execute` y puede agregar
funciones privadas de apoyo en este archivo.
"""

from dataclasses import dataclass

from routing_service.application.ports import NetworkGateway
from routing_service.domain.errors import DestinationNotFoundError, OriginNotFoundError
from routing_service.domain.results import PathResult, TraceStep
from routing_service.domain.strategies import PathFinder


@dataclass(frozen=True)
class Leg:
    edge_id: str
    source: str
    target: str
    weight: float


@dataclass(frozen=True)
class FewestHops:
    path: tuple[str, ...]
    hops: int
    cost: float


@dataclass(frozen=True)
class RouteReport:
    found: bool
    origin: str
    destination: str
    path: tuple[str, ...]
    total_cost: float | None
    hops: int | None
    legs: tuple[Leg, ...]
    fewest_hops: FewestHops | None
    message: str
    trace: tuple[TraceStep, ...]


def _minutes(value: float) -> str:
    return f"{value:g} min"


def _hops_label(hops: int) -> str:
    return f"{hops} tramo" if hops == 1 else f"{hops} tramos"


def _cost_and_hops(result: PathResult) -> tuple[float, int]:
    """Costo y tramos de un camino hallado; un `PathFinder` que no los informa viola su contrato."""
    if not result.found or result.total_cost is None or result.hops is None:
        raise RuntimeError("Un PathFinder devolvió un camino hallado sin costo o sin tramos.")
    return result.total_cost, result.hops


def _message(origin: str, cheapest: PathResult, fewest: FewestHops) -> str:
    cost, hops = _cost_and_hops(cheapest)
    if origin == cheapest.destination:
        return f"El origen y el destino son el mismo nodo ({origin}): costo {_minutes(cost)}."
    summary = f"Ruta de menor costo: {_minutes(cost)} en {_hops_label(hops)}"
    if fewest.path == cheapest.path:
        return f"{summary} (coincide con el camino de menos tramos)."
    return f"{summary} (el camino de menos tramos cuesta {_minutes(fewest.cost)})."


class FindCheapestRoute:
    """Ruta de menor costo (`path_finder`) comparada con la de menos tramos."""

    def __init__(
        self, gateway: NetworkGateway, path_finder: PathFinder, fewest_hops_finder: PathFinder
    ) -> None:
        self._gateway = gateway
        self._path_finder = path_finder
        self._fewest_hops_finder = fewest_hops_finder

    def execute(self, origin: str, destination: str, *, trace: bool = False) -> RouteReport:
        graph = self._gateway.load_graph()

        if not graph.has_node(origin):
            raise OriginNotFoundError(f"El origen '{origin}' no existe.", node_id=origin)
        if not graph.has_node(destination):
            raise DestinationNotFoundError(
                f"El destino '{destination}' no existe.", node_id=destination
            )

        cheapest = self._path_finder.find(graph, origin, destination, trace=trace)
        steps = cheapest.trace if trace else ()

        if not cheapest.found:
            return RouteReport(
                found=False,
                origin=origin,
                destination=destination,
                path=(),
                total_cost=None,
                hops=None,
                legs=(),
                fewest_hops=None,
                message=(
                    f"No hay ruta de {origin} a {destination}: "
                    "ningún camino de la red los conecta en ese sentido."
                ),
                trace=steps,
            )

        total_cost, hops = _cost_and_hops(cheapest)
        shortest = self._fewest_hops_finder.find(graph, origin, destination)
        shortest_cost, shortest_hops = _cost_and_hops(shortest)
        fewest = FewestHops(shortest.path, shortest_hops, shortest_cost)
        return RouteReport(
            found=True,
            origin=origin,
            destination=destination,
            path=cheapest.path,
            total_cost=total_cost,
            hops=hops,
            legs=tuple(
                Leg(arc.edge_id, arc.source, arc.target, arc.weight) for arc in cheapest.legs
            ),
            fewest_hops=fewest,
            message=_message(origin, cheapest, fewest),
            trace=steps,
        )
