"""Metadatos SQLAlchemy de la red. DUEÑO: carril F1-B (agrega las tablas aquí).

`Base.metadata` es el `target_metadata` de Alembic (alembic/env.py). Esquema exacto a crear:
docs/features/F1B-persistencia.md.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
