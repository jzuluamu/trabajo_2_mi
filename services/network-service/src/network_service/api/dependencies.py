"""Inyección de dependencias (DIP). DUEÑO: carril F1-C (agrega los proveedores de casos de uso).

`get_repository` es de la base y está CONGELADO: devuelve una única instancia por proceso,
construida por `infrastructure/factory.py` (F1-B decide si es memoria o PostgreSQL).
En pruebas se reemplaza con `app.dependency_overrides[get_repository]`.
"""

from functools import lru_cache

from network_service.application.ports import NetworkRepository
from network_service.config import get_settings
from network_service.infrastructure.factory import build_repository


@lru_cache
def _repository_singleton() -> NetworkRepository:
    return build_repository(get_settings())


def get_repository() -> NetworkRepository:
    return _repository_singleton()
