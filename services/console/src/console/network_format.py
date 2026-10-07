"""Transformaciones puras entre la red del contrato y lo que muestra o envía la consola.

Sin Streamlit ni HTTP: se prueba directamente. Las reglas de negocio (formato de ids, pesos,
duplicados) las valida network-service; aquí solo se da forma a los datos.
"""

import json
from typing import Any

from console.clients.http import ApiClientError

JsonDict = dict[str, Any]

TYPE_LABELS = {"BASE": "Base", "ZONE": "Zona"}
YES_WORDS = frozenset({"si", "sí", "s", "true", "1", "disponible"})
NO_WORDS = frozenset({"no", "n", "false", "0", "ocupado"})


class FormInputError(ValueError):
    """Dato del formulario que no se puede convertir al formato del contrato."""


def node_rows(network: JsonDict) -> list[JsonDict]:
    """Filas de la tabla de nodos: técnicos como texto `Ana ✔, Luis ✘`."""
    return [
        {
            "ID": node["id"],
            "Tipo": TYPE_LABELS.get(node["type"], node["type"]),
            "Nombre": node["name"],
            "Técnicos": ", ".join(
                f"{t['name']} ({t['id']}) {'✔' if t['available'] else '✘'}"
                for t in node.get("technicians", [])
            )
            or "—",
        }
        for node in network.get("nodes", [])
    ]


def edge_rows(network: JsonDict) -> list[JsonDict]:
    """Filas de la tabla de conexiones con peso en minutos y sentido legible."""
    return [
        {
            "ID": edge["id"],
            "Origen": edge["source"],
            "Destino": edge["target"],
            "Minutos": edge["weight"],
            "Sentido": "↔ ambos sentidos" if edge["bidirectional"] else "→ solo ida",
        }
        for edge in network.get("edges", [])
    ]


def parse_technicians(text: str) -> list[JsonDict]:
    """Convierte líneas `ID; Nombre; sí|no` en técnicos. La disponibilidad es opcional (sí)."""
    technicians: list[JsonDict] = []
    for number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = [part.strip() for part in line.split(";")]
        if len(parts) not in (2, 3):
            raise FormInputError(
                f"Técnico en la línea {number}: use el formato 'ID; Nombre; sí/no'."
            )
        available = True
        if len(parts) == 3:
            answer = parts[2].lower()
            if answer not in YES_WORDS | NO_WORDS:
                raise FormInputError(
                    f"Técnico en la línea {number}: la disponibilidad debe ser 'sí' o 'no'."
                )
            available = answer in YES_WORDS
        technicians.append({"id": parts[0], "name": parts[1], "available": available})
    return technicians


def node_payload(node_id: str, node_type: str, name: str, technicians_text: str) -> JsonDict:
    """Cuerpo de `POST /api/v1/nodes`. Las zonas no envían técnicos."""
    payload: JsonDict = {"id": node_id.strip(), "type": node_type, "name": name.strip()}
    if node_type == "BASE":
        payload["technicians"] = parse_technicians(technicians_text)
    elif technicians_text.strip():
        raise FormInputError("Solo las bases pueden tener técnicos.")
    return payload


def edge_payload(
    edge_id: str, source: str, target: str, weight: float, bidirectional: bool
) -> JsonDict:
    """Cuerpo de `POST /api/v1/edges`."""
    return {
        "id": edge_id.strip(),
        "source": source,
        "target": target,
        "weight": weight,
        "bidirectional": bidirectional,
    }


def parse_network_file(content: bytes, *, replace: bool) -> JsonDict:
    """Lee un JSON con `nodes` y `edges` (p. ej. seed/red_demo.json) para `/network/import`."""
    try:
        data = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FormInputError("El archivo no es un JSON válido.") from exc
    if not (
        isinstance(data, dict)
        and isinstance(data.get("nodes"), list)
        and isinstance(data.get("edges"), list)
    ):
        raise FormInputError("El archivo debe tener las listas 'nodes' y 'edges'.")
    return {"nodes": data["nodes"], "edges": data["edges"], "replace": replace}


def error_text(error: ApiClientError) -> str:
    """Mensaje legible del contrato; para VALIDATION_ERROR agrega los campos afectados."""
    fields = [
        str(item["field"]).removeprefix("body.")
        for item in error.details.get("errors", [])
        if isinstance(item, dict) and "field" in item
    ]
    location = ""
    if "section" in error.details and "index" in error.details:
        section = "nodo" if error.details["section"] == "nodes" else "conexión"
        location = f" (archivo: {section} #{int(error.details['index']) + 1})"
    suffix = f" Campos: {', '.join(fields)}." if fields else ""
    return f"{error.message}{location}{suffix}"
