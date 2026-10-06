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

## Fase 1 — Features en paralelo ⏳

Las 4 personas trabajan a la vez; cada una en su rama.

| Persona | Entregable | Checkpoint |
|---|---|---|
| P1 · F1 | Modelos SQLAlchemy + Alembic, repositorios, casos de uso, endpoints de nodos, conexiones, red e importación, validaciones y pruebas con PostgreSQL de prueba | Crear la red desde Swagger `:8001/docs` y ver cada error del contrato |
| P2 · F2 | `BreadthFirstReachability` en `domain/coverage/`, caso de uso, endpoint `/coverage` con `NetworkGateway` falso en las pruebas y traza | Pruebas de [04](04-algoritmos-bfs.md) en verde |
| P3 · F3 | `DijkstraPathFinder` en `domain/cheapest_path/`, casos de uso de ruta y de mejor atención, y endpoints | Pruebas de [05](05-algoritmos-dijkstra.md) en verde |
| P4 · F4 | Páginas de configuración (coordinador), cobertura y ruta (operador), visualización pyvis, todo contra clientes *mock* que siguen el contrato | Navegar la consola con datos falsos |

## Fase 2 — Integración ⏳

- `HttpNetworkGateway` en routing-service, que consume `GET /api/v1/network` con la clave interna y responde `NETWORK_UNAVAILABLE` si falla.
- La consola consume las APIs reales y carga la semilla con `POST /network/import`.
- Visualización que resalta la cobertura (nodos alcanzados) y la ruta (aristas del camino), y compara el camino de menor costo con el de menos tramos.

**Checkpoint:** demo de punta a punta en <http://localhost:8501>.

## Fase 3 — Aceptación y evidencia ⏳

- `make test-acceptance` con los 4 escenarios del brief: éxito, zona inexistente, red desconectada y peso inválido.
- Evidencia por feature en `docs/features/F*.md`: capturas, salidas de la API y trazas.
- Revisión final de la documentación frente al código.

**Checkpoint:** recorrer la guía completa [10](10-guia-prueba-manual.md).

## Fase 4 — Cambio de requisito docente ⏳

El requisito aún no se conoce. Puntos de extensión ya preparados:
- **Algoritmo nuevo** (A*, restricciones, k caminos): implementar `PathFinder` o `ReachabilityStrategy` sin tocar los casos de uso (OCP).
- **Nuevo atributo de arista** (distancia además de tiempo, costo monetario): agregarlo al contrato y elegir el peso con un parámetro.
- **Nueva regla de cobertura** (p. ej. "cubre si llega en ≤ N minutos"): es un caso de uso nuevo que combina Dijkstra con un umbral.

Al conocerse el requisito: crear un ADR, actualizar el contrato y abrir `docs/features/F4-consola.md` §cambio docente.
