# 0001 · Stack: Python 3.12 + FastAPI + PostgreSQL

- **Estado:** Aceptado
- **Fecha:** 2026-10-05

## Contexto
Hay 4 integrantes y el foco del curso es la algoritmia de grafos. Se necesita una API documentada ("consultar la red por API"), validación robusta, persistencia y ejecución idéntica en cualquier sistema operativo.

## Decisión
- **Python 3.12** en todos los servicios: un solo lenguaje y una sola toolchain.
- **FastAPI + Pydantic v2**: validación declarativa (pesos `> 0`, regex de ids) y OpenAPI/Swagger automático.
- **PostgreSQL 16 + SQLAlchemy 2 + Alembic**: restricciones `UNIQUE`/`CHECK`/FK como segunda barrera y migraciones versionadas.
- **uv** para gestionar dependencias con lockfile, y **Docker Compose** para orquestar.
- **pytest, ruff, mypy, bandit y pip-audit** como harness de calidad.

## Alternativas consideradas
- **Flask / Django REST:** más código manual (Flask) o más peso del necesario (Django) para 3 recursos.
- **SQLite:** bastaría técnicamente, porque un solo servicio persiste. Postgres demuestra mejores prácticas (concurrencia, restricciones, migraciones reales) sin costo extra en Docker.
- **Neo4j u otra base de grafos:** se descarta. El brief exige que **el equipo implemente** BFS y Dijkstra, y una base de grafos lo ocultaría.
- **Node/TypeScript o Java:** agregan curva de aprendizaje sin beneficio para el objetivo del curso.

## Consecuencias
- Toda persona puede contribuir en cualquier servicio.
- Los algoritmos se escriben en Python puro (`heapq`, `collections.deque`), sin librerías de grafos.
