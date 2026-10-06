"""Composición del repositorio concreto. DUEÑO: carril F1-B.

Base de F1: devuelve el repositorio en memoria (los datos se pierden al reiniciar el contenedor).
F1-B reemplaza el cuerpo de `build_repository` para devolver el repositorio SQLAlchemy usando
`settings.database_url`. Ningún otro archivo debe cambiar para activar PostgreSQL.
"""

from network_service.application.ports import NetworkRepository
from network_service.config import Settings
from network_service.infrastructure.memory_repository import InMemoryNetworkRepository


def build_repository(settings: Settings) -> NetworkRepository:
    del settings  # F1-B lo usará (settings.database_url)
    return InMemoryNetworkRepository()
