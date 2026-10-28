"""network-service y routing-service falsos servidos con `httpx.MockTransport` (F1 y F2).

Reproduce la forma de las respuestas y de los errores de docs/03-api.md; no reimplementa todas
las reglas, solo las que las pruebas de la consola necesitan observar.
"""

import json
from typing import Any

import httpx

DEMO: dict[str, Any] = {
    "nodes": [
        {
            "id": "B_NORTE",
            "type": "BASE",
            "name": "Base Norte",
            "technicians": [
                {"id": "T01", "name": "Ana", "available": True},
                {"id": "T02", "name": "Luis", "available": False},
            ],
        },
        {"id": "Z_CENTRO", "type": "ZONE", "name": "Centro", "technicians": []},
    ],
    "edges": [
        {"id": "E01", "source": "B_NORTE", "target": "Z_CENTRO", "weight": 30.0,
         "bidirectional": True},
    ],
}  # fmt: skip


def _error(status: int, code: str, message: str, **details: Any) -> httpx.Response:
    return httpx.Response(status, json={"code": code, "message": message, "details": details})


class FakeNetworkService:
    def __init__(self, role: str = "coordinator", *, empty: bool = False) -> None:
        self.role = role
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: dict[str, dict[str, Any]] = {}
        self.requests: list[tuple[str, str]] = []
        self.down = False
        self.uncovered: set[str] = set()
        self.unknown_base = False  # routing-service responde ORIGIN_NOT_FOUND
        self.coverage_queries: list[dict[str, str]] = []
        if not empty:
            self._load(DEMO, replace=True)

    @property
    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self.handle)

    def _load(self, data: dict[str, Any], *, replace: bool) -> None:
        if replace:
            self.nodes, self.edges = {}, {}
        for node in data["nodes"]:
            self.nodes[node["id"]] = {"technicians": [], **node}
        for edge in data["edges"]:
            self.edges[edge["id"]] = {"bidirectional": True, **edge}

    def network(self) -> dict[str, Any]:
        return {
            "nodes": [self.nodes[key] for key in sorted(self.nodes)],
            "edges": [self.edges[key] for key in sorted(self.edges)],
        }

    def coverage(self, params: dict[str, str]) -> httpx.Response:
        """routing-service falso: desde toda base se alcanzan las zonas salvo `uncovered`."""
        base, zone = params["base"], params.get("zone")
        self.coverage_queries.append(params)
        if self.unknown_base or base not in self.nodes:
            return _error(404, "ORIGIN_NOT_FOUND", f"La base '{base}' no existe.", node_id=base)
        zones = sorted(k for k, n in self.nodes.items() if n["type"] == "ZONE")
        reachable = [
            {"node_id": z, "type": "ZONE", "hops": 1} for z in zones if z not in self.uncovered
        ]
        zone_info = None
        if zone:
            covered = zone not in self.uncovered
            zone_info = {
                "id": zone,
                "covered": covered,
                "hops": 1 if covered else None,
                "message": f"{zone} está cubierta desde {base} (1 tramo)."
                if covered
                else f"{zone} no está cubierta: no hay conexión desde {base}.",
            }
        trace = None
        if params.get("trace") == "true":
            trace = [
                {"step": 0, "action": "enqueue", "node": base, "data": {"hops": 0}},
                {"step": 1, "action": "visit", "node": base, "data": {"hops": 0}},
            ]
        body = {
            "base": base,
            "reachable": reachable,
            "unreachable_zones": sorted(self.uncovered),
            "zone": zone_info,
            "trace": trace,
        }
        return httpx.Response(200, json=body)

    def handle(self, request: httpx.Request) -> httpx.Response:
        method, path = request.method, request.url.path
        self.requests.append((method, path))
        if path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        if self.down:
            raise httpx.ConnectError("refused", request=request)
        if path == "/api/v1/auth/whoami":
            return httpx.Response(200, json={"role": self.role})
        if (method, path) == ("GET", "/api/v1/coverage"):
            return self.coverage(dict(request.url.params))
        writes = method != "GET"
        if writes and self.role != "coordinator":
            return _error(403, "FORBIDDEN", f"El rol '{self.role}' no tiene permiso.")
        body = json.loads(request.content) if request.content else {}
        if (method, path) == ("GET", "/api/v1/network"):
            return httpx.Response(200, json=self.network())
        if (method, path) == ("POST", "/api/v1/nodes"):
            if body["id"] in self.nodes:
                msg = f"Ya existe un nodo con id '{body['id']}'."
                return _error(409, "DUPLICATE_ID", msg, node_id=body["id"])
            self.nodes[body["id"]] = {"technicians": [], **body}
            return httpx.Response(201, json=self.nodes[body["id"]])
        if (method, path) == ("POST", "/api/v1/edges"):
            if not 0 < body["weight"] <= 1440:
                msg = (
                    f"El peso de la conexión '{body['id']}' debe ser mayor que 0 y menor o "
                    "igual a 1440 minutos."
                )
                return _error(422, "INVALID_WEIGHT", msg, edge_id=body["id"])
            self.edges[body["id"]] = body
            return httpx.Response(201, json=body)
        if method == "DELETE" and path.startswith("/api/v1/nodes/"):
            node_id = path.rsplit("/", 1)[1]
            uses = sorted(
                e["id"] for e in self.edges.values() if node_id in (e["source"], e["target"])
            )
            if uses:
                msg = f"El nodo '{node_id}' tiene conexiones; elimínelas primero."
                return _error(409, "NODE_IN_USE", msg, node_id=node_id, edge_ids=uses)
            del self.nodes[node_id]
            return httpx.Response(204)
        if method == "DELETE" and path.startswith("/api/v1/edges/"):
            del self.edges[path.rsplit("/", 1)[1]]
            return httpx.Response(204)
        if (method, path) == ("POST", "/api/v1/network/import"):
            for index, edge in enumerate(body["edges"]):
                if edge["weight"] <= 0:
                    return _error(
                        422,
                        "INVALID_WEIGHT",
                        "Peso inválido.",
                        edge_id=edge["id"],
                        section="edges",
                        index=index,
                    )
            self._load(body, replace=body.get("replace", False))
            return httpx.Response(
                201, json={"nodes": len(body["nodes"]), "edges": len(body["edges"])}
            )
        return _error(404, "NOT_FOUND", "Ruta no encontrada.")
