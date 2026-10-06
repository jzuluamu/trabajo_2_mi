import pytest

from network_service.application.use_cases import (
    DeleteEdge,
    DeleteNode,
    GetNetwork,
    GetNode,
    ImportNetwork,
    ListEdges,
    ListNodes,
    RegisterEdge,
    RegisterNode,
)
from network_service.domain.errors import (
    DuplicateEdgeError,
    DuplicateIdError,
    EdgeNotFoundError,
    InvalidFieldError,
    InvalidWeightError,
    NodeInUseError,
    NodeNotFoundError,
    SelfLoopError,
)
from network_service.domain.models import Edge, Node, NodeType, Technician
from network_service.infrastructure.memory_repository import InMemoryNetworkRepository


def _base(node_id: str = "B_NORTE", *, technicians: tuple[Technician, ...] = ()) -> Node:
    return Node(id=node_id, type=NodeType.BASE, name="Base Norte", technicians=technicians)


def _zone(node_id: str = "Z_CENTRO") -> Node:
    return Node(id=node_id, type=NodeType.ZONE, name="Centro")


def _edge(
    edge_id: str = "E01",
    source: str = "B_NORTE",
    target: str = "Z_CENTRO",
    *,
    weight: float = 30,
    bidirectional: bool = True,
) -> Edge:
    return Edge(
        id=edge_id, source=source, target=target, weight=weight, bidirectional=bidirectional
    )


# --- RegisterNode ------------------------------------------------------------------------------


def test_register_node_saves_and_returns_it() -> None:
    repo = InMemoryNetworkRepository()
    node = _base()

    result = RegisterNode(repo).execute(node)

    assert result == node
    assert repo.get_node("B_NORTE") == node


def test_register_node_rejects_duplicate_node_id() -> None:
    repo = InMemoryNetworkRepository()
    RegisterNode(repo).execute(_base())

    with pytest.raises(DuplicateIdError) as excinfo:
        RegisterNode(repo).execute(_base())

    error = excinfo.value
    assert error.code == "DUPLICATE_ID"
    assert error.details == {"node_id": "B_NORTE"}


def test_register_node_rejects_technician_duplicated_in_another_base() -> None:
    repo = InMemoryNetworkRepository()
    RegisterNode(repo).execute(_base(technicians=(Technician(id="T01", name="Ana"),)))
    other_base = _base(node_id="B_SUR", technicians=(Technician(id="T01", name="Luis"),))

    with pytest.raises(DuplicateIdError) as excinfo:
        RegisterNode(repo).execute(other_base)

    error = excinfo.value
    assert error.code == "DUPLICATE_ID"
    assert error.details == {"technician_id": "T01"}


def test_register_node_delegates_validation() -> None:
    repo = InMemoryNetworkRepository()
    zone_with_technicians = Node(
        id="Z_CENTRO",
        type=NodeType.ZONE,
        name="Centro",
        technicians=(Technician(id="T01", name="Ana"),),
    )

    with pytest.raises(InvalidFieldError) as excinfo:
        RegisterNode(repo).execute(zone_with_technicians)

    assert excinfo.value.details == {"field": "technicians"}


# --- RegisterEdge ------------------------------------------------------------------------------


def _repo_with_nodes() -> InMemoryNetworkRepository:
    repo = InMemoryNetworkRepository()
    repo.add_node(_base())
    repo.add_node(_zone())
    return repo


def test_register_edge_saves_and_returns_it() -> None:
    repo = _repo_with_nodes()
    edge = _edge()

    result = RegisterEdge(repo).execute(edge)

    assert result == edge
    assert repo.get_edge("E01") == edge


def test_register_edge_rejects_duplicate_edge_id() -> None:
    repo = _repo_with_nodes()
    RegisterEdge(repo).execute(_edge())

    with pytest.raises(DuplicateIdError) as excinfo:
        RegisterEdge(repo).execute(_edge(edge_id="E01", source="Z_CENTRO", target="B_NORTE"))

    error = excinfo.value
    assert error.code == "DUPLICATE_ID"
    assert error.details == {"edge_id": "E01"}


def test_register_edge_rejects_missing_source() -> None:
    repo = _repo_with_nodes()
    edge = _edge(source="B_FANTASMA")

    with pytest.raises(NodeNotFoundError) as excinfo:
        RegisterEdge(repo).execute(edge)

    error = excinfo.value
    assert error.code == "NODE_NOT_FOUND"
    assert error.details == {"node_id": "B_FANTASMA"}


def test_register_edge_rejects_missing_target() -> None:
    repo = _repo_with_nodes()
    edge = _edge(target="Z_FANTASMA")

    with pytest.raises(NodeNotFoundError) as excinfo:
        RegisterEdge(repo).execute(edge)

    error = excinfo.value
    assert error.code == "NODE_NOT_FOUND"
    assert error.details == {"node_id": "Z_FANTASMA"}


def test_register_edge_rejects_missing_source_before_target() -> None:
    repo = InMemoryNetworkRepository()
    edge = _edge(source="B_FANTASMA", target="Z_FANTASMA")

    with pytest.raises(NodeNotFoundError) as excinfo:
        RegisterEdge(repo).execute(edge)

    assert excinfo.value.details == {"node_id": "B_FANTASMA"}


def test_register_edge_rejects_same_pair_duplicate() -> None:
    repo = _repo_with_nodes()
    RegisterEdge(repo).execute(_edge())

    with pytest.raises(DuplicateEdgeError) as excinfo:
        RegisterEdge(repo).execute(_edge(edge_id="E02"))

    error = excinfo.value
    assert error.code == "DUPLICATE_EDGE"
    assert error.details == {"edge_id": "E01"}


def test_register_edge_rejects_inverse_bidirectional_duplicate() -> None:
    repo = _repo_with_nodes()
    RegisterEdge(repo).execute(_edge(bidirectional=True))

    with pytest.raises(DuplicateEdgeError):
        RegisterEdge(repo).execute(
            _edge(edge_id="E02", source="Z_CENTRO", target="B_NORTE", bidirectional=False)
        )


def test_register_edge_allows_inverse_when_both_one_way() -> None:
    repo = _repo_with_nodes()
    RegisterEdge(repo).execute(_edge(bidirectional=False))

    result = RegisterEdge(repo).execute(
        _edge(edge_id="E02", source="Z_CENTRO", target="B_NORTE", bidirectional=False)
    )

    assert result.id == "E02"
    assert len(repo.list_edges()) == 2


def test_register_edge_rejects_invalid_weight() -> None:
    repo = _repo_with_nodes()
    edge = _edge(weight=-1)

    with pytest.raises(InvalidWeightError) as excinfo:
        RegisterEdge(repo).execute(edge)

    assert excinfo.value.code == "INVALID_WEIGHT"


def test_register_edge_rejects_self_loop() -> None:
    repo = _repo_with_nodes()
    edge = _edge(source="B_NORTE", target="B_NORTE")

    with pytest.raises(SelfLoopError) as excinfo:
        RegisterEdge(repo).execute(edge)

    assert excinfo.value.code == "SELF_LOOP"


# --- GetNode / DeleteNode / DeleteEdge -----------------------------------------------------


def test_get_node_returns_existing_node() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_base())

    assert GetNode(repo).execute("B_NORTE") == _base()


def test_get_node_raises_not_found() -> None:
    repo = InMemoryNetworkRepository()

    with pytest.raises(NodeNotFoundError) as excinfo:
        GetNode(repo).execute("B_FANTASMA")

    error = excinfo.value
    assert error.code == "NODE_NOT_FOUND"
    assert error.details == {"node_id": "B_FANTASMA"}


def test_delete_node_raises_not_found() -> None:
    repo = InMemoryNetworkRepository()

    with pytest.raises(NodeNotFoundError) as excinfo:
        DeleteNode(repo).execute("B_FANTASMA")

    assert excinfo.value.code == "NODE_NOT_FOUND"


def test_delete_node_raises_node_in_use_with_sorted_edge_ids() -> None:
    repo = _repo_with_nodes()
    repo.add_edge(_edge(edge_id="E02", source="B_NORTE", target="Z_CENTRO", bidirectional=False))
    repo.add_edge(_edge(edge_id="E01", source="Z_CENTRO", target="B_NORTE", bidirectional=False))

    with pytest.raises(NodeInUseError) as excinfo:
        DeleteNode(repo).execute("B_NORTE")

    error = excinfo.value
    assert error.code == "NODE_IN_USE"
    assert error.details == {"node_id": "B_NORTE", "edge_ids": ["E01", "E02"]}


def test_delete_node_removes_node_without_edges() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_base())

    DeleteNode(repo).execute("B_NORTE")

    assert repo.get_node("B_NORTE") is None


def test_delete_edge_raises_not_found() -> None:
    repo = InMemoryNetworkRepository()

    with pytest.raises(EdgeNotFoundError) as excinfo:
        DeleteEdge(repo).execute("E_FANTASMA")

    error = excinfo.value
    assert error.code == "EDGE_NOT_FOUND"
    assert error.details == {"edge_id": "E_FANTASMA"}


def test_delete_edge_removes_existing_edge() -> None:
    repo = _repo_with_nodes()
    repo.add_edge(_edge())

    DeleteEdge(repo).execute("E01")

    assert repo.get_edge("E01") is None


# --- ListNodes / ListEdges / GetNetwork -----------------------------------------------------


def test_list_nodes_returns_nodes_ordered_by_id() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_base(node_id="B_SUR"))
    repo.add_node(_base(node_id="B_NORTE"))

    assert [node.id for node in ListNodes(repo).execute()] == ["B_NORTE", "B_SUR"]


def test_list_edges_returns_edges_ordered_by_id() -> None:
    repo = _repo_with_nodes()
    repo.add_edge(_edge(edge_id="E02", target="Z_CENTRO"))
    repo.add_edge(_edge(edge_id="E01", target="Z_CENTRO"))

    assert [edge.id for edge in ListEdges(repo).execute()] == ["E01", "E02"]


def test_get_network_returns_nodes_and_edges_ordered() -> None:
    repo = _repo_with_nodes()
    repo.add_edge(_edge())

    network = GetNetwork(repo).execute()

    assert [node.id for node in network.nodes] == ["B_NORTE", "Z_CENTRO"]
    assert [edge.id for edge in network.edges] == ["E01"]


# --- ImportNetwork -----------------------------------------------------------------------------


def _demo_nodes() -> list[Node]:
    return [
        Node(
            id="B_NORTE",
            type=NodeType.BASE,
            name="Base Norte",
            technicians=(
                Technician(id="T01", name="Ana", available=True),
                Technician(id="T02", name="Luis", available=False),
            ),
        ),
        Node(
            id="B_SUR",
            type=NodeType.BASE,
            name="Base Sur",
            technicians=(Technician(id="T03", name="Marta", available=True),),
        ),
        Node(
            id="B_OESTE",
            type=NodeType.BASE,
            name="Base Oeste",
            technicians=(Technician(id="T04", name="Pedro", available=False),),
        ),
        Node(id="Z_ALAMEDA", type=NodeType.ZONE, name="Alameda"),
        Node(id="Z_BOSQUE", type=NodeType.ZONE, name="Bosque"),
        Node(id="Z_CENTRO", type=NodeType.ZONE, name="Centro"),
        Node(id="Z_COLINA", type=NodeType.ZONE, name="Colina"),
        Node(id="Z_DELICIAS", type=NodeType.ZONE, name="Delicias"),
        Node(id="Z_ESTACION", type=NodeType.ZONE, name="Estación"),
        Node(id="Z_FUENTE", type=NodeType.ZONE, name="Fuente"),
        Node(id="Z_ISLA", type=NodeType.ZONE, name="Isla"),
    ]


def _demo_edges() -> list[Edge]:
    return [
        Edge(id="E01", source="B_NORTE", target="Z_CENTRO", weight=30),
        Edge(id="E02", source="B_NORTE", target="Z_ALAMEDA", weight=5),
        Edge(id="E03", source="Z_ALAMEDA", target="Z_BOSQUE", weight=5),
        Edge(id="E04", source="Z_BOSQUE", target="Z_CENTRO", weight=5),
        Edge(id="E05", source="Z_CENTRO", target="Z_COLINA", weight=10),
        Edge(id="E06", source="B_SUR", target="Z_DELICIAS", weight=8),
        Edge(id="E07", source="Z_DELICIAS", target="Z_COLINA", weight=12),
        Edge(id="E08", source="Z_DELICIAS", target="Z_ESTACION", weight=7, bidirectional=False),
        Edge(id="E09", source="B_OESTE", target="Z_FUENTE", weight=6),
    ]


def test_import_network_demo_seed_replaces_and_counts() -> None:
    repo = InMemoryNetworkRepository()

    summary = ImportNetwork(repo).execute(_demo_nodes(), _demo_edges(), replace=True)

    assert summary.nodes == 11
    assert summary.edges == 9
    assert len(repo.list_nodes()) == 11
    assert len(repo.list_edges()) == 9


def test_import_network_replace_true_clears_previous_state() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_zone(node_id="Z_VIEJA"))

    ImportNetwork(repo).execute([_base()], [], replace=True)

    assert repo.get_node("Z_VIEJA") is None
    assert repo.get_node("B_NORTE") is not None


def test_import_network_replace_false_adds_to_existing_state() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_zone(node_id="Z_VIEJA"))

    ImportNetwork(repo).execute([_base()], [], replace=False)

    assert repo.get_node("Z_VIEJA") is not None
    assert repo.get_node("B_NORTE") is not None


def test_import_network_edge_error_reports_section_and_index_and_keeps_repo_intact() -> None:
    repo = InMemoryNetworkRepository()
    nodes = [_base(), _zone(), _zone(node_id="Z_BOSQUE")]
    edges = [
        _edge(edge_id="E01", target="Z_CENTRO"),
        _edge(edge_id="E02", target="Z_BOSQUE"),
        _edge(edge_id="E03", source="Z_FANTASMA", target="Z_CENTRO"),
    ]

    with pytest.raises(NodeNotFoundError) as excinfo:
        ImportNetwork(repo).execute(nodes, edges, replace=True)

    error = excinfo.value
    assert error.details["section"] == "edges"
    assert error.details["index"] == 2
    assert repo.list_nodes() == []
    assert repo.list_edges() == []


def test_import_network_duplicate_node_in_batch_reports_section_and_index() -> None:
    repo = InMemoryNetworkRepository()
    nodes = [_base(node_id="B_SUR"), _base(node_id="B_SUR")]

    with pytest.raises(DuplicateIdError) as excinfo:
        ImportNetwork(repo).execute(nodes, [], replace=True)

    error = excinfo.value
    assert error.details["section"] == "nodes"
    assert error.details["index"] == 1
    assert repo.list_nodes() == []


def test_import_network_replace_false_allows_edge_referencing_existing_node() -> None:
    repo = InMemoryNetworkRepository()
    repo.add_node(_base())
    repo.add_node(_zone())

    summary = ImportNetwork(repo).execute([], [_edge()], replace=False)

    assert summary.edges == 1
    assert repo.get_edge("E01") is not None
