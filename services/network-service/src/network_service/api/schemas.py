"""Esquemas HTTP y conversiones entre payloads y entidades de dominio."""

from pydantic import BaseModel, ConfigDict, Field

from network_service.domain.models import (
    Edge,
    ImportSummary,
    Network,
    Node,
    NodeType,
    Technician,
)


class TechnicianIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    name: str = Field(max_length=256)
    available: bool = True

    def to_domain(self) -> Technician:
        return Technician(id=self.id, name=self.name, available=self.available)


class TechnicianOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    name: str = Field(max_length=256)
    available: bool = True

    @classmethod
    def from_domain(cls, technician: Technician) -> "TechnicianOut":
        return cls(
            id=technician.id,
            name=technician.name,
            available=technician.available,
        )


class NodeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    type: NodeType
    name: str = Field(max_length=256)
    technicians: list[TechnicianIn] = Field(default_factory=list, max_length=100)

    def to_domain(self) -> Node:
        return Node(
            id=self.id,
            type=self.type,
            name=self.name,
            technicians=tuple(technician.to_domain() for technician in self.technicians),
        )


class NodeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    type: NodeType
    name: str = Field(max_length=256)
    technicians: list[TechnicianOut]

    @classmethod
    def from_domain(cls, node: Node) -> "NodeOut":
        return cls(
            id=node.id,
            type=node.type,
            name=node.name,
            technicians=[TechnicianOut.from_domain(technician) for technician in node.technicians],
        )


class EdgeIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    source: str = Field(max_length=256)
    target: str = Field(max_length=256)
    weight: float
    bidirectional: bool = True

    def to_domain(self) -> Edge:
        return Edge(
            id=self.id,
            source=self.source,
            target=self.target,
            weight=self.weight,
            bidirectional=self.bidirectional,
        )


class EdgeOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(max_length=256)
    source: str = Field(max_length=256)
    target: str = Field(max_length=256)
    weight: float
    bidirectional: bool = True

    @classmethod
    def from_domain(cls, edge: Edge) -> "EdgeOut":
        return cls(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            weight=edge.weight,
            bidirectional=edge.bidirectional,
        )


class NetworkOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[NodeOut]
    edges: list[EdgeOut]

    @classmethod
    def from_domain(cls, network: Network) -> "NetworkOut":
        return cls(
            nodes=[NodeOut.from_domain(node) for node in network.nodes],
            edges=[EdgeOut.from_domain(edge) for edge in network.edges],
        )


class NetworkImportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: list[NodeIn] = Field(max_length=1000)
    edges: list[EdgeIn] = Field(max_length=5000)
    replace: bool = False


class ImportSummaryOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nodes: int
    edges: int

    @classmethod
    def from_domain(cls, summary: ImportSummary) -> "ImportSummaryOut":
        return cls(nodes=summary.nodes, edges=summary.edges)
