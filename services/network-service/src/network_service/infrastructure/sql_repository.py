"""Repositorio PostgreSQL con SQLAlchemy 2.0. DUEÑO: carril F1-B.

Implementa el puerto `NetworkRepository` (`application/ports.py`) y pasa sin cambios la
suite de contrato `tests/contract/repository_contract.py`. No valida reglas de negocio
(eso es F1-A); solo almacena y consulta. Consultas siempre parametrizadas (API SQLAlchemy).
"""

from collections.abc import Sequence

from sqlalchemy import Engine, delete, insert, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from network_service.domain.errors import DuplicateIdError
from network_service.domain.models import Edge, Node, NodeType, Technician
from network_service.infrastructure.orm import EdgeRow, NodeRow, TechnicianRow

_DUPLICATE_SQLSTATE = "23505"
_DUPLICATE_MESSAGE = "El identificador ya existe."


class SqlAlchemyNetworkRepository:
    """Persistencia en PostgreSQL. Cada método usa su propia sesión/transacción."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    # --- lectura ---------------------------------------------------------------------
    def get_node(self, node_id: str) -> Node | None:
        with Session(self._engine) as session:
            row = session.get(NodeRow, node_id)
            if row is None:
                return None
            return _node_from_rows(row, _technicians_of(session, node_id))

    def list_nodes(self) -> list[Node]:
        with Session(self._engine) as session:
            rows = session.scalars(select(NodeRow).order_by(NodeRow.id)).all()
            return [_node_from_rows(row, _technicians_of(session, row.id)) for row in rows]

    def get_edge(self, edge_id: str) -> Edge | None:
        with Session(self._engine) as session:
            row = session.get(EdgeRow, edge_id)
            return _edge_from_row(row) if row is not None else None

    def list_edges(self) -> list[Edge]:
        with Session(self._engine) as session:
            rows = session.scalars(select(EdgeRow).order_by(EdgeRow.id)).all()
            return [_edge_from_row(row) for row in rows]

    def technician_exists(self, technician_id: str) -> bool:
        with Session(self._engine) as session:
            row = session.scalars(
                select(TechnicianRow.id).where(TechnicianRow.id == technician_id).limit(1)
            ).first()
            return row is not None

    # --- escritura -------------------------------------------------------------------
    def add_node(self, node: Node) -> None:
        try:
            with Session(self._engine) as session, session.begin():
                _insert_nodes(session, [node])
        except IntegrityError as exc:
            _raise_duplicate_or_rethrow(exc)

    def delete_node(self, node_id: str) -> None:
        with Session(self._engine) as session, session.begin():
            session.execute(delete(TechnicianRow).where(TechnicianRow.node_id == node_id))
            session.execute(delete(NodeRow).where(NodeRow.id == node_id))

    def add_edge(self, edge: Edge) -> None:
        try:
            with Session(self._engine) as session, session.begin():
                _insert_edges(session, [edge])
        except IntegrityError as exc:
            _raise_duplicate_or_rethrow(exc)

    def delete_edge(self, edge_id: str) -> None:
        with Session(self._engine) as session, session.begin():
            session.execute(delete(EdgeRow).where(EdgeRow.id == edge_id))

    def save_network(self, nodes: Sequence[Node], edges: Sequence[Edge], *, replace: bool) -> None:
        try:
            with Session(self._engine) as session, session.begin():
                if replace:
                    session.execute(delete(EdgeRow))
                    session.execute(delete(TechnicianRow))
                    session.execute(delete(NodeRow))
                _insert_nodes(session, nodes)
                _insert_edges(session, edges)
        except IntegrityError as exc:
            _raise_duplicate_or_rethrow(exc)


# --- apoyo ---------------------------------------------------------------------------


def _technicians_of(session: Session, node_id: str) -> Sequence[TechnicianRow]:
    return session.scalars(
        select(TechnicianRow)
        .where(TechnicianRow.node_id == node_id)
        .order_by(TechnicianRow.position)
    ).all()


def _node_from_rows(node_row: NodeRow, tech_rows: Sequence[TechnicianRow]) -> Node:
    return Node(
        id=node_row.id,
        type=NodeType(node_row.type),
        name=node_row.name,
        technicians=tuple(
            Technician(id=t.id, name=t.name, available=t.available) for t in tech_rows
        ),
    )


def _edge_from_row(row: EdgeRow) -> Edge:
    return Edge(
        id=row.id,
        source=row.source,
        target=row.target,
        weight=float(row.weight),
        bidirectional=row.bidirectional,
    )


def _insert_nodes(session: Session, nodes: Sequence[Node]) -> None:
    for node in nodes:
        session.execute(insert(NodeRow).values(id=node.id, type=node.type.value, name=node.name))
        for position, technician in enumerate(node.technicians):
            session.execute(
                insert(TechnicianRow).values(
                    id=technician.id,
                    node_id=node.id,
                    position=position,
                    name=technician.name,
                    available=technician.available,
                )
            )


def _insert_edges(session: Session, edges: Sequence[Edge]) -> None:
    for edge in edges:
        session.execute(
            insert(EdgeRow).values(
                id=edge.id,
                source=edge.source,
                target=edge.target,
                weight=edge.weight,
                bidirectional=edge.bidirectional,
            )
        )


def _raise_duplicate_or_rethrow(exc: IntegrityError) -> None:
    """Traduce unicidad violada (PK o UQ, sqlstate 23505) a `DuplicateIdError`."""
    if getattr(exc.orig, "sqlstate", None) == _DUPLICATE_SQLSTATE:
        raise DuplicateIdError(_DUPLICATE_MESSAGE) from exc
    raise exc
