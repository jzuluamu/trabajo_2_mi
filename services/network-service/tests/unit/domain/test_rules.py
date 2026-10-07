import math

import pytest

from network_service.domain.errors import (
    DuplicateIdError,
    InvalidFieldError,
    InvalidWeightError,
    SelfLoopError,
)
from network_service.domain.models import Edge, Node, NodeType, Technician
from network_service.domain.rules import (
    edges_conflict,
    is_identifier,
    validate_edge,
    validate_identifier,
    validate_name,
    validate_node,
    validate_weight,
)

# --- validate_identifier --------------------------------------------------------------------


@pytest.mark.parametrize("value", ["B1", "Z_CENTRO", "A-1", "A" * 32])
def test_validate_identifier_accepts_valid_values(value: str) -> None:
    validate_identifier(value, "id")


@pytest.mark.parametrize("value", ["", "A" * 33, "b1", "Z CENTRO", "ZÁREA", "Z.1"])
def test_validate_identifier_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidFieldError) as excinfo:
        validate_identifier(value, "id")

    error = excinfo.value
    assert error.code == "VALIDATION_ERROR"
    assert error.details == {"field": "id"}
    if value:
        assert value not in error.message


def test_validate_identifier_is_case_sensitive() -> None:
    with pytest.raises(InvalidFieldError):
        validate_identifier("b1", "id")


# --- validate_name ---------------------------------------------------------------------------


@pytest.mark.parametrize("value", ["", "   ", "A" * 81])
def test_validate_name_rejects_invalid_values(value: str) -> None:
    with pytest.raises(InvalidFieldError) as excinfo:
        validate_name(value, "name")

    error = excinfo.value
    assert error.code == "VALIDATION_ERROR"
    assert error.details == {"field": "name"}


def test_validate_name_accepts_max_length() -> None:
    validate_name("A" * 80, "name")


# --- validate_weight --------------------------------------------------------------------------


@pytest.mark.parametrize("weight", [0, -1, 1440.01, math.inf, math.nan])
def test_validate_weight_rejects_invalid_values(weight: float) -> None:
    with pytest.raises(InvalidWeightError) as excinfo:
        validate_weight(weight, "E01")

    error = excinfo.value
    assert error.code == "INVALID_WEIGHT"
    assert error.details == {"edge_id": "E01"}


@pytest.mark.parametrize("weight", [0.5, 1440])
def test_validate_weight_accepts_valid_values(weight: float) -> None:
    validate_weight(weight, "E01")


# --- validate_node ----------------------------------------------------------------------------


def test_validate_node_rejects_zone_with_technicians() -> None:
    zone = Node(
        id="Z_CENTRO",
        type=NodeType.ZONE,
        name="Centro",
        technicians=(Technician(id="T01", name="Ana"),),
    )

    with pytest.raises(InvalidFieldError) as excinfo:
        validate_node(zone)

    error = excinfo.value
    assert error.code == "VALIDATION_ERROR"
    assert error.details == {"field": "technicians"}


def test_validate_node_rejects_invalid_technician_id() -> None:
    base = Node(
        id="B_NORTE",
        type=NodeType.BASE,
        name="Base Norte",
        technicians=(Technician(id="t01", name="Ana"),),
    )

    with pytest.raises(InvalidFieldError) as excinfo:
        validate_node(base)

    error = excinfo.value
    assert error.code == "VALIDATION_ERROR"
    assert error.details == {"field": "technicians[0].id"}


def test_validate_node_rejects_duplicated_technician_id() -> None:
    base = Node(
        id="B_NORTE",
        type=NodeType.BASE,
        name="Base Norte",
        technicians=(Technician(id="T01", name="Ana"), Technician(id="T01", name="Luis")),
    )

    with pytest.raises(DuplicateIdError) as excinfo:
        validate_node(base)

    error = excinfo.value
    assert error.code == "DUPLICATE_ID"
    assert error.details == {"technician_id": "T01"}


def test_validate_node_accepts_valid_base_with_technicians() -> None:
    base = Node(
        id="B_NORTE",
        type=NodeType.BASE,
        name="Base Norte",
        technicians=(Technician(id="T01", name="Ana"), Technician(id="T02", name="Luis")),
    )

    validate_node(base)


def test_validate_node_reports_invalid_id_before_invalid_name() -> None:
    node = Node(id="z centro", type=NodeType.ZONE, name="")

    with pytest.raises(InvalidFieldError) as excinfo:
        validate_node(node)

    assert excinfo.value.details == {"field": "id"}


# --- validate_edge ----------------------------------------------------------------------------


def test_validate_edge_rejects_self_loop() -> None:
    edge = Edge(id="E01", source="B_NORTE", target="B_NORTE", weight=10)

    with pytest.raises(SelfLoopError) as excinfo:
        validate_edge(edge)

    error = excinfo.value
    assert error.code == "SELF_LOOP"
    assert error.details == {"edge_id": "E01"}


def test_validate_edge_reports_invalid_id_before_self_loop() -> None:
    edge = Edge(id="e 01", source="B_NORTE", target="B_NORTE", weight=10)

    with pytest.raises(InvalidFieldError) as excinfo:
        validate_edge(edge)

    assert excinfo.value.details == {"field": "id"}


def test_validate_edge_reports_self_loop_before_invalid_weight() -> None:
    edge = Edge(id="E01", source="B_NORTE", target="B_NORTE", weight=-1)

    with pytest.raises(SelfLoopError):
        validate_edge(edge)


def test_validate_edge_accepts_valid_edge() -> None:
    edge = Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=30)

    validate_edge(edge)


# --- edges_conflict ---------------------------------------------------------------------------


def _edge(source: str, target: str, *, bidirectional: bool = True) -> Edge:
    return Edge(id="E99", source=source, target=target, weight=10, bidirectional=bidirectional)


def test_edges_conflict_same_pair_is_true() -> None:
    new = _edge("B_NORTE", "Z_CENTRO")
    existing = _edge("B_NORTE", "Z_CENTRO")

    assert edges_conflict(new, existing) is True


@pytest.mark.parametrize(
    ("new_bidirectional", "existing_bidirectional"),
    [(True, True), (True, False), (False, True)],
)
def test_edges_conflict_inverse_pair_with_bidirectional_is_true(
    new_bidirectional: bool, existing_bidirectional: bool
) -> None:
    new = _edge("Z_CENTRO", "B_NORTE", bidirectional=new_bidirectional)
    existing = _edge("B_NORTE", "Z_CENTRO", bidirectional=existing_bidirectional)

    assert edges_conflict(new, existing) is True


def test_edges_conflict_inverse_pair_both_one_way_is_false() -> None:
    new = _edge("Z_CENTRO", "B_NORTE", bidirectional=False)
    existing = _edge("B_NORTE", "Z_CENTRO", bidirectional=False)

    assert edges_conflict(new, existing) is False


def test_edges_conflict_different_pairs_is_false() -> None:
    new = _edge("B_SUR", "Z_DELICIAS")
    existing = _edge("B_NORTE", "Z_CENTRO")

    assert edges_conflict(new, existing) is False


@pytest.mark.parametrize(
    ("value", "expected"), [("Z_CENTRO", True), ("<script>", False), ("", False)]
)
def test_is_identifier(value: str, expected: bool) -> None:
    assert is_identifier(value) is expected
