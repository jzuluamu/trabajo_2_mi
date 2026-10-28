"""Gateway HTTP hacia network-service: obtiene la red y la entrega como `Graph`."""

import logging
from typing import Any

import httpx
from fastapi import status

from routing_service.core.errors import AppError
from routing_service.domain.graph import Graph, Node, NodeType, Technician

logger = logging.getLogger(__name__)

NETWORK_PATH = "/api/v1/network"


def _unavailable() -> AppError:
    return AppError(
        "NETWORK_UNAVAILABLE",
        "No se pudo obtener la red de cobertura. Intente de nuevo más tarde.",
        status.HTTP_503_SERVICE_UNAVAILABLE,
    )


class HttpNetworkGateway:
    """Implementa `NetworkGateway` consultando `GET /api/v1/network` con la clave `internal`."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout
        self._transport = transport

    def load_graph(self) -> Graph:
        return self._build_graph(self._fetch())

    def _fetch(self) -> dict[str, Any]:
        try:
            with httpx.Client(timeout=self._timeout, transport=self._transport) as client:
                response = client.get(
                    f"{self._base_url}{NETWORK_PATH}", headers={"X-API-Key": self._api_key}
                )
            if response.status_code != httpx.codes.OK:
                logger.error("network-service respondió HTTP %s", response.status_code)
                raise _unavailable()
            payload = response.json()
        except httpx.HTTPError as exc:
            logger.error("No se pudo contactar a network-service: %s", type(exc).__name__)
            raise _unavailable() from exc
        except ValueError as exc:
            logger.error("network-service devolvió JSON inválido")
            raise _unavailable() from exc
        if not isinstance(payload, dict):
            logger.error("network-service devolvió una estructura inesperada")
            raise _unavailable()
        return payload

    @staticmethod
    def _build_graph(payload: dict[str, Any]) -> Graph:
        graph = Graph()
        try:
            for item in payload["nodes"]:
                technicians = tuple(
                    Technician(t["id"], t["name"], bool(t["available"]))
                    for t in item.get("technicians", [])
                )
                graph.add_node(Node(item["id"], NodeType(item["type"]), item["name"], technicians))
            for edge in payload["edges"]:
                graph.add_edge(
                    edge["id"],
                    edge["source"],
                    edge["target"],
                    float(edge["weight"]),
                    bidirectional=bool(edge["bidirectional"]),
                )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            logger.error("La red recibida no cumple el contrato: %s", type(exc).__name__)
            raise _unavailable() from exc
        return graph
