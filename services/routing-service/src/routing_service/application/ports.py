"""Puertos de salida de la capa de aplicación (DIP); la implementación vive en infrastructure."""

from typing import Protocol

from routing_service.domain.graph import Graph


class NetworkGateway(Protocol):
    """Obtiene la red vigente desde network-service y la entrega como `Graph`."""

    def load_graph(self) -> Graph: ...
