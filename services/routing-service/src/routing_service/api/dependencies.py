"""Proveedores de dependencias (DIP): los casos de uso reciben sus colaboradores inyectados."""

from typing import Annotated

from fastapi import Depends

from routing_service.application.attention import FindBestAttention
from routing_service.application.coverage import CheckCoverage
from routing_service.application.ports import NetworkGateway
from routing_service.application.routes import FindCheapestRoute
from routing_service.config import Settings, get_settings
from routing_service.domain.cheapest_path.dijkstra import DijkstraPathFinder
from routing_service.domain.cheapest_path.fewest_hops import BreadthFirstPathFinder
from routing_service.domain.coverage.bfs import BreadthFirstReachability
from routing_service.domain.strategies import PathFinder, ReachabilityStrategy
from routing_service.infrastructure.network_gateway import HttpNetworkGateway


def provide_gateway(settings: Annotated[Settings, Depends(get_settings)]) -> NetworkGateway:
    return HttpNetworkGateway(
        str(settings.network_service_url),
        settings.internal_api_key.get_secret_value(),
        settings.request_timeout_seconds,
    )


def provide_reachability() -> ReachabilityStrategy:
    return BreadthFirstReachability()


def provide_check_coverage(
    gateway: Annotated[NetworkGateway, Depends(provide_gateway)],
    strategy: Annotated[ReachabilityStrategy, Depends(provide_reachability)],
) -> CheckCoverage:
    return CheckCoverage(gateway, strategy)


def provide_path_finder() -> PathFinder:
    return DijkstraPathFinder()


def provide_fewest_hops_finder() -> PathFinder:
    return BreadthFirstPathFinder()


def provide_find_cheapest_route(
    gateway: Annotated[NetworkGateway, Depends(provide_gateway)],
    path_finder: Annotated[PathFinder, Depends(provide_path_finder)],
    fewest_hops_finder: Annotated[PathFinder, Depends(provide_fewest_hops_finder)],
) -> FindCheapestRoute:
    return FindCheapestRoute(gateway, path_finder, fewest_hops_finder)


def provide_find_best_attention(
    gateway: Annotated[NetworkGateway, Depends(provide_gateway)],
    path_finder: Annotated[PathFinder, Depends(provide_path_finder)],
) -> FindBestAttention:
    return FindBestAttention(gateway, path_finder)
