from console.clients.http import HttpServiceClient


class NetworkClient(HttpServiceClient):
    """Cliente de network-service (Feature 1). Fase 1 agrega nodos, conexiones y red."""

    service_name = "network-service"

    def whoami(self) -> str:
        return str(self._request("GET", "/api/v1/auth/whoami")["role"])
