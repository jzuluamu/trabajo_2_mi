"""Endpoints de nodos — IMPLEMENTA: carril F1-C (docs/features/F1C-api-rest.md).

El router ya está registrado en `main.py`; F1-C solo agrega endpoints aquí.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/nodes", tags=["nodes"])
