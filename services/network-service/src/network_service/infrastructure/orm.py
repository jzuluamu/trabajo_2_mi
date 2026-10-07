"""Metadatos SQLAlchemy de la red. DUEÑO: carril F1-B (agrega las tablas aquí).

`Base.metadata` es el `target_metadata` de Alembic (alembic/env.py). Esquema exacto a crear:
docs/features/F1B-persistencia.md.
"""

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class NodeRow(Base):
    """Fila de `nodes`: base o zona."""

    __tablename__ = "nodes"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    type: Mapped[str] = mapped_column(
        String(4), CheckConstraint("type IN ('BASE','ZONE')", name="ck_nodes_type")
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class TechnicianRow(Base):
    """Fila de `technicians`: técnico de una base, con su orden (`position`)."""

    __tablename__ = "technicians"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    node_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("nodes.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(nullable=False)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)


class EdgeRow(Base):
    """Fila de `edges`: trayecto `source`→`target` de `weight` minutos."""

    __tablename__ = "edges"
    __table_args__ = (
        CheckConstraint("weight > 0 AND weight <= 1440", name="ck_edges_weight_range"),
        CheckConstraint("source <> target", name="ck_edges_no_self_loop"),
        UniqueConstraint("source", "target", name="uq_edges_source_target"),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    source: Mapped[str] = mapped_column(
        String(32), ForeignKey("nodes.id", ondelete="RESTRICT"), nullable=False
    )
    target: Mapped[str] = mapped_column(
        String(32), ForeignKey("nodes.id", ondelete="RESTRICT"), nullable=False
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    bidirectional: Mapped[bool] = mapped_column(Boolean, nullable=False)
