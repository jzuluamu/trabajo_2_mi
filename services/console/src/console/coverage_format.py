"""Transformaciones puras de la respuesta de cobertura (F2) a lo que muestra la consola."""

from typing import Any

from console.network_format import TYPE_LABELS, JsonDict

ACTION_LABELS = {"enqueue": "Encola", "visit": "Visita"}


def nodes_of_type(network: JsonDict, node_type: str) -> list[JsonDict]:
    return [node for node in network.get("nodes", []) if node["type"] == node_type]


def _names(network: JsonDict) -> dict[str, str]:
    return {node["id"]: node["name"] for node in network.get("nodes", [])}


def reachable_rows(network: JsonDict, report: JsonDict) -> list[JsonDict]:
    names = _names(network)
    return [
        {
            "ID": item["node_id"],
            "Nombre": names.get(item["node_id"], item["node_id"]),
            "Tipo": TYPE_LABELS.get(item["type"], item["type"]),
            "Tramos": item["hops"],
        }
        for item in report["reachable"]
    ]


def unreachable_rows(network: JsonDict, report: JsonDict) -> list[JsonDict]:
    names = _names(network)
    return [{"ID": zone, "Nombre": names.get(zone, zone)} for zone in report["unreachable_zones"]]


def trace_rows(report: JsonDict) -> list[JsonDict]:
    """Traza del BFS tal como la devuelve la API: paso, acción, nodo y tramos."""
    rows: list[JsonDict] = []
    for item in report.get("trace") or []:
        data: dict[str, Any] = item.get("data", {})
        rows.append(
            {
                "Paso": item["step"],
                "Acción": ACTION_LABELS.get(item["action"], item["action"]),
                "Nodo": item["node"],
                "Tramos": data.get("hops"),
                "Desde": data.get("from", ""),
            }
        )
    return rows
