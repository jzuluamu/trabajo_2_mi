"""Proveedores de dependencias (DIP): los casos de uso reciben sus colaboradores inyectados."""

from typing import Annotated

from fastapi import Depends

from routing_service.application.coverage import CheckCoverage
from routing_service.application.ports import NetworkGateway
from routing_service.config import Settings, get_settings
from routing_service.domain.coverage.bfs import BreadthFirstReachability
from routing_service.domain.strategies import ReachabilityStrategy
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
