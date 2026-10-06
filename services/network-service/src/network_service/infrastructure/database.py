"""Creación del engine SQLAlchemy. DUEÑO: carril F1-B."""

from sqlalchemy import Engine, create_engine


def create_db_engine(database_url: str) -> Engine:
    """Crea el engine sin abrir conexión (seguro en pruebas unitarias con URL falsa)."""
    return create_engine(database_url, pool_pre_ping=True)
