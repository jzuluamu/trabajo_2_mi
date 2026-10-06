"""Reglas de validación del dominio — IMPLEMENTA: carril F1-A.

Especificación: docs/features/F1A-dominio-casos-de-uso.md.

Las firmas están CONGELADAS; el cuerpo de cada función se reemplaza por la implementación.
Mensajes exactos y orden de validación: ver la especificación F1-A.
"""

from network_service.domain.models import Edge, Node


def validate_identifier(value: str, field: str) -> None:
    """Exige `value` con formato `ID_PATTERN` (1-32 caracteres A-Z, 0-9, '_' o '-').

    Lanza `InvalidFieldError(details={"field": field})`. No incluir `value` en el mensaje.
    """
    raise NotImplementedError("F1-A")


def validate_name(value: str, field: str) -> None:
    """Exige 1..NAME_MAX_LENGTH caracteres tras `strip()` (no vacío ni solo espacios).

    Lanza `InvalidFieldError(details={"field": field})`.
    """
    raise NotImplementedError("F1-A")


def validate_weight(weight: float, edge_id: str) -> None:
    """Exige peso finito con 0 < weight <= WEIGHT_MAX_MINUTES.

    Lanza `InvalidWeightError(details={"edge_id": edge_id})`.
    """
    raise NotImplementedError("F1-A")


def validate_node(node: Node) -> None:
    """Valida un nodo completo, en este orden:

    1. `validate_identifier(node.id, "id")`
    2. `validate_name(node.name, "name")`
    3. Si `node.type` es ZONE y tiene técnicos → `InvalidFieldError(field="technicians")`.
    4. Por cada técnico i: `validate_identifier(t.id, f"technicians[{i}].id")` y
       `validate_name(t.name, f"technicians[{i}].name")`.
    5. Ids de técnico repetidos dentro del mismo nodo → `DuplicateIdError(technician_id=...)`.
    """
    raise NotImplementedError("F1-A")


def validate_edge(edge: Edge) -> None:
    """Valida la forma de una conexión, en este orden:

    1. `validate_identifier` de `id`, `source` y `target` (fields "id", "source", "target").
    2. `source == target` → `SelfLoopError(details={"edge_id": edge.id})`.
    3. `validate_weight(edge.weight, edge.id)`.
    """
    raise NotImplementedError("F1-A")


def edges_conflict(new: Edge, existing: Edge) -> bool:
    """True si `new` duplica la conexión física `existing` (docs/02 §Duplicados):

    - mismo par dirigido (source, target), o
    - par inverso (new.source == existing.target y new.target == existing.source) cuando
      `new` o `existing` es bidireccional.
    Ignora `id` y `weight`.
    """
    raise NotImplementedError("F1-A")
