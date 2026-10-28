# F2 · Consulta de cobertura (BFS)

- **Servicio:** `routing-service` (`domain/coverage/`) · **Estado:** ✅ Terminada (con evidencia)
- **Lea antes:** [04-algoritmos-bfs](../04-algoritmos-bfs.md), [02-modelo-de-grafo](../02-modelo-de-grafo.md), [03-api](../03-api.md#get-apiv1coveragebaseb_nortezonez_centrotracetrue--f2)

## Valor de negocio
El operador sabe si una solicitud está dentro de una cobertura posible y qué zonas pueden alcanzarse desde una base.

## Criterios de aceptación
- [x] Recibe la base (y opcionalmente una zona) y lista el alcance con `hops` mínimos.
- [x] BFS **implementado por el equipo** (`BreadthFirstReachability`, que implementa `ReachabilityStrategy`), justificado en [04](../04-algoritmos-bfs.md).
- [x] Resultado legible ante:
  - una red desconectada (`unreachable_zones`);
  - un origen inexistente (`ORIGIN_NOT_FOUND`) o que no es base (`INVALID_ORIGIN`);
  - una zona inexistente (`ZONE_NOT_FOUND`);
  - una zona sin conexión (`covered=false` con `message`).
- [x] `trace=true` devuelve la traza, que coincide con el ejemplo pequeño de [04](../04-algoritmos-bfs.md).
- [x] Pruebas unitarias con todos los casos de la checklist de [04](../04-algoritmos-bfs.md).
- [x] La red se obtiene de network-service por HTTP con la clave `internal`; si no responde, `NETWORK_UNAVAILABLE` (503).
- [x] Pestaña **Cobertura** en la consola para ambos roles.

## Diseño (por capas, `services/routing-service/src/routing_service/`)

| Capa | Archivo | Responsabilidad |
|---|---|---|
| domain | `domain/coverage/bfs.py` | `BreadthFirstReachability`: algoritmo puro con `deque`, sin I/O |
| domain | `domain/errors.py` | `OriginNotFoundError`, `InvalidOriginError`, `ZoneNotFoundError` |
| application | `application/coverage.py` | `CheckCoverage(gateway, strategy)` y `CoverageReport`; valida en el orden origen → tipo de origen → zona |
| infrastructure | `infrastructure/network_gateway.py` | `HttpNetworkGateway`: `GET /api/v1/network` y conversión a `Graph` |
| api | `api/coverage.py`, `api/dependencies.py` | Endpoint, esquemas, roles e inyección de dependencias |

Decisiones:
- **Orden de los errores:** `ORIGIN_NOT_FOUND` (404), luego `INVALID_ORIGIN` (422), luego `ZONE_NOT_FOUND` (404). Una "zona" que en realidad es una base también es `ZONE_NOT_FOUND`.
- **Traza:** `TraceStep(step, action, node, data)` con `action` ∈ `enqueue`/`visit`. `step` es la columna "Paso" de la tabla de [04](../04-algoritmos-bfs.md): el origen se encola en el paso 0 y cada nodo que sale de la cola abre un paso con su `visit` y los `enqueue` de sus vecinos nuevos (`data` lleva `hops` y, en `enqueue`, `from`).
- **Fallos de network-service** (timeout, conexión, estado ≠ 200, JSON o estructura inválidos) se registran en el log y el cliente solo recibe `NETWORK_UNAVAILABLE`, sin reflejar el detalle.
- **Pesos inválidos** en la red recibida no se enmascaran: `InvalidWeightError` se propaga (defensa en profundidad que usará F3).

## Evidencia

Verificado el 2026-10-28 sobre `feature/F2-consulta-cobertura`.

**Harness completo** (ruff, formato, mypy strict, bandit, pip-audit y pytest) en verde en los tres servicios: network-service 242 pruebas (99,7 %), routing-service 84 (100 %) y console 74 (99,1 %).

> **Dependencias:** antes de F2, `pip-audit` ya fallaba en los tres servicios por avisos nuevos contra `uv.lock`. Se resolvió con un PR aparte (`chore/actualizar-dependencias`) que sube `certifi` a 2026.10.23, `filelock` a 4.2.4, `opentelemetry-api` a 1.45.1 y, en la consola, `streamlit` a 1.66.1 y `pillow` a 13.0.0 (`pillow` 12.3.0 tenía avisos y `streamlit` 1.65.0 no permitía actualizarlo). El harness de F2 se verificó con esos `uv.lock`.

**Pruebas por capa** (`services/routing-service/tests/`):
- `unit/domain/coverage/test_bfs.py`: hops de la red demo, otra componente, zona aislada, arista de un solo sentido, ciclos, origen inexistente y traza idéntica a la tabla de [04](../04-algoritmos-bfs.md).
- `unit/application/test_coverage.py`: orden y contenido del reporte, mensajes en singular y plural, zona no cubierta, los tres errores y su orden (con fakes, sin el BFS real).
- `unit/infrastructure/test_network_gateway.py`: conversión de la red demo con `httpx.MockTransport`, clave `X-API-Key`, timeout, conexión, 401/403/404/500, JSON y estructura inválidos.
- `unit/api/test_coverage_api.py`: BFS y gateway reales de punta a punta (con network-service simulado): contrato, traza, 401, 403 (rol `internal`), 404, 422, 503.

**Humo contra Docker** (base limpia, proyecto Compose aislado con `NETWORK_PORT=18001` y `ROUTING_PORT=18002`):

```text
==> smoke F2 contra http://127.0.0.1:18002/api/v1
  OK    importar seed/red_demo.json -> 201
  OK    cobertura de B_NORTE -> Z_FUENTE y Z_ISLA sin cobertura
  OK    Z_CENTRO cubierta desde B_NORTE en 1 tramo
  OK    Z_FUENTE no cubierta -> 200 con covered=false
  OK    trace=true devuelve la traza del BFS
  OK    base inexistente -> 404 ORIGIN_NOT_FOUND
  OK    origen de tipo zona -> 422 INVALID_ORIGIN
  OK    zona inexistente -> 404 ZONE_NOT_FOUND
  OK    sin X-API-Key -> 401
OK: smoke F2 en verde
```

**Consola:** la pestaña **Cobertura** (`console/components/coverage_view.py`) la ven el operador y el coordinador. Se elige la base, una zona opcional y si se quiere la traza. Muestra el mensaje de la zona (verde si está cubierta, ámbar si no), los indicadores, la tabla de nodos alcanzables con sus tramos, las zonas sin cobertura y, opcionalmente, la traza del BFS. Está cubierta con `AppTest` en `services/console/tests/test_coverage_ui.py`.
