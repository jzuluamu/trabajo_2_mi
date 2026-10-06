"""Reglas de validación del dominio — IMPLEMENTA: carril F1-A.

Especificación: docs/features/F1A-dominio-casos-de-uso.md.

Las firmas están CONGELADAS; el cuerpo de cada función se reemplaza por la implementación.
Mensajes exactos y orden de validación: ver la especificación F1-A.
"""

import math
import re

from network_service.domain.errors import (
    DuplicateIdError,
    InvalidFieldError,
    InvalidWeightError,
    SelfLoopError,
)
from network_service.domain.models import (
    ID_PATTERN,
    NAME_MAX_LENGTH,
    WEIGHT_MAX_MINUTES,
    Edge,
    Node,
    NodeType,
)


def validate_identifier(value: str, field: str) -> None:
    """Exige `value` con formato `ID_PATTERN` (1-32 caracteres A-Z, 0-9, '_' o '-').

    Lanza `InvalidFieldError(details={"field": field})`. No incluir `value` en el mensaje.
    """
    if re.fullmatch(ID_PATTERN, value) is None:
        raise InvalidFieldError(
            f"El campo '{field}' debe tener entre 1 y 32 caracteres: A-Z, 0-9, '_' o '-'.",
            field=field,
        )


def validate_name(value: str, field: str) -> None:
    """Exige 1..NAME_MAX_LENGTH caracteres tras `strip()` (no vacío ni solo espacios).

    Lanza `InvalidFieldError(details={"field": field})`.
    """
    if not 1 <= len(value.strip()) <= NAME_MAX_LENGTH:
        raise InvalidFieldError(
            f"El campo '{field}' debe tener entre 1 y {NAME_MAX_LENGTH} caracteres.",
            field=field,
        )


def validate_weight(weight: float, edge_id: str) -> None:
    """Exige peso finito con 0 < weight <= WEIGHT_MAX_MINUTES.

    Lanza `InvalidWeightError(details={"edge_id": edge_id})`.
    """
    if not (math.isfinite(weight) and 0 < weight <= WEIGHT_MAX_MINUTES):
        raise InvalidWeightError(
            f"El peso de la conexión '{edge_id}' debe ser mayor que 0 y menor o "
            f"igual a {int(WEIGHT_MAX_MINUTES)} minutos.",
            edge_id=edge_id,
        )


def validate_node(node: Node) -> None:
    """Valida un nodo completo, en este orden:

    1. `validate_identifier(node.id, "id")`
    2. `validate_name(node.name, "name")`
    3. Si `node.type` es ZONE y tiene técnicos → `InvalidFieldError(field="technicians")`.
    4. Por cada técnico i: `validate_identifier(t.id, f"technicians[{i}].id")` y
       `validate_name(t.name, f"technicians[{i}].name")`.
    5. Ids de técnico repetidos dentro del mismo nodo → `DuplicateIdError(technician_id=...)`.
    """
    validate_identifier(node.id, "id")
    validate_name(node.name, "name")
    if node.type is NodeType.ZONE and node.technicians:
        raise InvalidFieldError("Solo las bases pueden tener técnicos.", field="technicians")
    for i, technician in enumerate(node.technicians):
        validate_identifier(technician.id, f"technicians[{i}].id")
        validate_name(technician.name, f"technicians[{i}].name")
    seen_technician_ids: set[str] = set()
    for technician in node.technicians:
        if technician.id in seen_technician_ids:
            raise DuplicateIdError(
                f"El técnico '{technician.id}' está repetido en el nodo '{node.id}'.",
                technician_id=technician.id,
            )
        seen_technician_ids.add(technician.id)


def validate_edge(edge: Edge) -> None:
    """Valida la forma de una conexión, en este orden:

    1. `validate_identifier` de `id`, `source` y `target` (fields "id", "source", "target").
    2. `source == target` → `SelfLoopError(details={"edge_id": edge.id})`.
    3. `validate_weight(edge.weight, edge.id)`.
    """
    validate_identifier(edge.id, "id")
    validate_identifier(edge.source, "source")
    validate_identifier(edge.target, "target")
    if edge.source == edge.target:
        raise SelfLoopError(
            f"La conexión '{edge.id}' no puede unir un nodo consigo mismo.", edge_id=edge.id
        )
    validate_weight(edge.weight, edge.id)


def edges_conflict(new: Edge, existing: Edge) -> bool:
    """True si `new` duplica la conexión física `existing` (docs/02 §Duplicados):

    - mismo par dirigido (source, target), o
    - par inverso (new.source == existing.target y new.target == existing.source) cuando
      `new` o `existing` es bidireccional.
    Ignora `id` y `weight`.
    """
    if new.source == existing.source and new.target == existing.target:
        return True
    if new.source == existing.target and new.target == existing.source:
        return bool(new.bidirectional or existing.bidirectional)
    return False
