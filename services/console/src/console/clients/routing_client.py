from typing import Any

from console.clients.http import HttpServiceClient

JsonDict = dict[str, Any]


class RoutingClient(HttpServiceClient):
    """Cliente de routing-service (Features 2 y 3). Contrato: docs/03-api.md."""

    service_name = "routing-service"

    def get_coverage(self, base: str, zone: str | None = None, *, trace: bool = False) -> JsonDict:
        params: dict[str, str] = {"base": base, "trace": "true" if trace else "false"}
        if zone:
            params["zone"] = zone
        report: JsonDict = self._request("GET", "/api/v1/coverage", params=params)
        return report
