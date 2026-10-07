from typing import Any
from urllib.parse import quote

from console.clients.http import HttpServiceClient

JsonDict = dict[str, Any]


class NetworkClient(HttpServiceClient):
    """Cliente de network-service (Feature 1). Contrato: docs/03-api.md."""

    service_name = "network-service"

    def whoami(self) -> str:
        return str(self._request("GET", "/api/v1/auth/whoami")["role"])

    def get_network(self) -> JsonDict:
        network: JsonDict = self._request("GET", "/api/v1/network")
        return network

    def create_node(self, node: JsonDict) -> JsonDict:
        created: JsonDict = self._request("POST", "/api/v1/nodes", json=node)
        return created

    def create_edge(self, edge: JsonDict) -> JsonDict:
        created: JsonDict = self._request("POST", "/api/v1/edges", json=edge)
        return created

    def delete_node(self, node_id: str) -> None:
        self._request("DELETE", f"/api/v1/nodes/{quote(node_id, safe='')}")

    def delete_edge(self, edge_id: str) -> None:
        self._request("DELETE", f"/api/v1/edges/{quote(edge_id, safe='')}")

    def import_network(self, payload: JsonDict) -> JsonDict:
        summary: JsonDict = self._request("POST", "/api/v1/network/import", json=payload)
        return summary
