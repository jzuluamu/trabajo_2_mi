"""Congela las interfaces de la base de F1 que usan otros carriles (F1-A ↔ F1-C ↔ F1-B).

Si esta prueba falla, se cambió una firma compartida: revierta o abra un PR `contract-change`
aprobado por los dueños de los tres carriles (docs/features/F1-red-cobertura.md).
"""

import inspect
from collections.abc import Callable
from typing import Any

import pytest

from network_service.application import use_cases
from network_service.domain import rules


def _signature(func: Callable[..., Any]) -> str:
    return str(inspect.signature(func))


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("validate_identifier", "(value: str, field: str) -> None"),
        ("validate_name", "(value: str, field: str) -> None"),
        ("validate_weight", "(weight: float, edge_id: str) -> None"),
        ("validate_node", "(node: network_service.domain.models.Node) -> None"),
        ("validate_edge", "(edge: network_service.domain.models.Edge) -> None"),
        (
            "edges_conflict",
            "(new: network_service.domain.models.Edge, "
            "existing: network_service.domain.models.Edge) -> bool",
        ),
    ],
)
def test_rule_signatures_are_frozen(name: str, expected: str) -> None:
    assert _signature(getattr(rules, name)) == expected


NODE = "network_service.domain.models.Node"
EDGE = "network_service.domain.models.Edge"


@pytest.mark.parametrize(
    ("name", "repository_port", "execute"),
    [
        ("RegisterNode", "NetworkRepository", f"(self, node: {NODE}) -> {NODE}"),
        ("RegisterEdge", "NetworkRepository", f"(self, edge: {EDGE}) -> {EDGE}"),
        ("GetNode", "NetworkReader", f"(self, node_id: str) -> {NODE}"),
        ("ListNodes", "NetworkReader", f"(self) -> list[{NODE}]"),
        ("ListEdges", "NetworkReader", f"(self) -> list[{EDGE}]"),
        ("DeleteNode", "NetworkRepository", "(self, node_id: str) -> None"),
        ("DeleteEdge", "NetworkRepository", "(self, edge_id: str) -> None"),
        ("GetNetwork", "NetworkReader", "(self) -> network_service.domain.models.Network"),
        (
            "ImportNetwork",
            "NetworkRepository",
            f"(self, nodes: collections.abc.Sequence[{NODE}], "
            f"edges: collections.abc.Sequence[{EDGE}], *, replace: bool) "
            "-> network_service.domain.models.ImportSummary",
        ),
    ],
)
def test_use_case_signatures_are_frozen(name: str, repository_port: str, execute: str) -> None:
    use_case = getattr(use_cases, name)

    init = inspect.signature(use_case.__init__)
    assert list(init.parameters) == ["self", "repository"]
    assert repository_port in str(init.parameters["repository"].annotation)
    assert _signature(use_case.execute) == execute
