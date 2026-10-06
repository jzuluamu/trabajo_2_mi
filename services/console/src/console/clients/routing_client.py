from console.clients.http import HttpServiceClient


class RoutingClient(HttpServiceClient):
    """Cliente de routing-service (Features 2 y 3). Fase 1 agrega cobertura y ruta."""

    service_name = "routing-service"
