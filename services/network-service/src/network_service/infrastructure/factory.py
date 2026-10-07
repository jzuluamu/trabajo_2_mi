"""Composición del repositorio concreto. DUEÑO: carril F1-B.

F1-B activa PostgreSQL: construye el engine con `settings.database_url` y devuelve el
repositorio SQLAlchemy. Crear el engine no abre conexión.
"""

from network_service.application.ports import NetworkRepository
from network_service.config import Settings
from network_service.infrastructure.database import create_db_engine
from network_service.infrastructure.sql_repository import SqlAlchemyNetworkRepository


def build_repository(settings: Settings) -> NetworkRepository:
    return SqlAlchemyNetworkRepository(create_db_engine(settings.database_url.get_secret_value()))
