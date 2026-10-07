# 09 · Fases y roadmap

Cada fase termina con un **checkpoint humano**: alguien del equipo ejecuta la guía de prueba y confirma que funciona antes de pasar a la siguiente.

## Fase 0 — Fundaciones ✅

**Entregables:**
- README con el objetivo del proyecto y toda la documentación de `docs/`.
- `AGENTS.md` y `CLAUDE.md`.
- `.env.example` y `make env`.
- `docker-compose.yml` (db, network, routing, console) endurecido, y `docker-compose.test.yml`.
- `Makefile` y la CI.
- Esqueletos de los tres servicios:
  - `/health` en cada uno;
  - formato de errores;
  - seguridad por rol con `X-API-Key`, y `/auth/whoami` en network-service;
  - consola con inicio de sesión y estado de servicios.
- Dominio compartido de routing-service (`Graph`, resultados y estrategias) con pruebas.
- Contrato de la API congelado ([03-api.md](03-api.md)).
- Datos semilla (`seed/red_demo.json`).

**Checkpoint:** `make env && make up`. Los 3 servicios aparecen *healthy*, la consola abre, el login con la clave de operador o coordinador funciona y `make test` pasa. Ver [10-guia-prueba-manual.md](10-guia-prueba-manual.md#fase-0).

## Ajuste de alcance (decisión del equipo)

El proyecto se enfoca **solo en Feature 1 (Red de cobertura)**. F2, F3 y F4 completas, la aceptación y el cambio docente quedan **fuera del alcance actual**. Sus documentos (`docs/04`, `docs/05`, `F2`–`F4`) se conservan como diseño de referencia.

## Base de F1 (congelada) ✅

La construyó el integrador sobre la Fase 0 para que los carriles trabajen sin pisarse:
- entidades (`domain/models.py`), errores con código (`domain/errors.py`) y puertos (`application/ports.py`);
- repositorio en memoria de referencia y **suite de contrato** del repositorio;
- firmas de reglas y casos de uso, vigiladas por `tests/unit/test_frozen_interfaces.py`;
- mapeo de errores a HTTP y routers ya registrados;
- esqueleto de Alembic con migraciones al arrancar, y PostgreSQL de pruebas en el harness.

También corrige el `Makefile`: antes `make test` imprimía OK **sin ejecutar pruebas**. Ver [07](07-testing-y-harness.md).

## Fase 1 — F1 en 3 carriles paralelos ✅

| Carril | Entregable | Rama | Checkpoint |
|---|---|---|---|
| **F1-A** | Reglas de dominio y 9 casos de uso | `feature/F1A-dominio-casos-de-uso` | `make test-network` con 100 % en `rules.py` y `use_cases.py` |
| **F1-B** | Tablas, migración `0001` y `SqlAlchemyNetworkRepository` | `feature/F1B-persistencia` | La suite de contrato pasa contra PostgreSQL; `make reset && make up` aplica la migración |
| **F1-C** | Esquemas, 9 endpoints, autorización por rol e inyección de dependencias | `feature/F1C-api-rest` | Swagger muestra las 9 rutas; las pruebas con fakes están en verde |

Cada carril pasa `make test` por sí solo, así que **se fusionan en cualquier orden**. Especificaciones: [F1-A](features/F1A-dominio-casos-de-uso.md), [F1-B](features/F1B-persistencia.md) y [F1-C](features/F1C-api-rest.md). Prompts para los agentes: [F1-prompts](features/F1-prompts.md).

## Fase 1.D — Integración de F1 ✅

Empieza cuando A, B y C están en `main`:
- prueba punta a punta;
- `make smoke-f1` contra Docker, incluida la persistencia;
- interfaz mínima en la consola (ver la red; como coordinador, registrar y cargar la red demo);
- evidencia y documentación al día.

Especificación: [F1-D](features/F1D-integracion.md).

**Checkpoint:** `make reset && make up && make test && make smoke-f1`, más el recorrido manual de la guía [10](10-guia-prueba-manual.md), sección F1.

## Fuera del alcance actual ⛔

Si el alcance se amplía, se retoman en este orden:
1. F2, cobertura con BFS ([04](04-algoritmos-bfs.md));
2. F3, menor costo con Dijkstra ([05](05-algoritmos-dijkstra.md));
3. F4 completa;
4. la aceptación de los 4 escenarios del brief;
5. el cambio de requisito docente.

Los puntos de extensión siguen preparados: `ReachabilityStrategy` y `PathFinder` en routing-service.
