"""Crea las tablas de la red (F1-B). Esquema exacto: docs/features/F1B-persistencia.md."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "nodes",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("type", sa.String(4), nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.CheckConstraint("type IN ('BASE','ZONE')", name="ck_nodes_type"),
    )
    op.create_table(
        "technicians",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "node_id",
            sa.String(32),
            sa.ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer, nullable=False),
        sa.Column("name", sa.String(80), nullable=False),
        sa.Column("available", sa.Boolean, nullable=False),
    )
    op.create_table(
        "edges",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column(
            "source",
            sa.String(32),
            sa.ForeignKey("nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "target",
            sa.String(32),
            sa.ForeignKey("nodes.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("weight", sa.Float, nullable=False),
        sa.Column("bidirectional", sa.Boolean, nullable=False),
        sa.CheckConstraint("weight > 0 AND weight <= 1440", name="ck_edges_weight_range"),
        sa.CheckConstraint("source <> target", name="ck_edges_no_self_loop"),
        sa.UniqueConstraint("source", "target", name="uq_edges_source_target"),
    )


def downgrade() -> None:
    op.drop_table("edges")
    op.drop_table("technicians")
    op.drop_table("nodes")
