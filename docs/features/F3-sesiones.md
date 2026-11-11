# F3 · Qué hace cada integrante (4 sesiones, cada una desde su PC)

F3 se construye en **4 carriles**, cada uno en su rama y con **sus propios archivos**, sobre una **base congelada** que ya está en `main`. Visión general y tabla de propiedad de archivos: [F3-menor-costo.md](F3-menor-costo.md).

| Sesión | Quién | Carril | Rama |
|---|---|---|---|
| 1 | Juan Pablo | F3-A Algoritmos (Dijkstra y menos tramos) | `feature/F3A-algoritmos` |
| 2 | Alexander | F3-B Casos de uso | `feature/F3B-casos-de-uso` |
| 3 | Juan Andrés | F3-C API REST | `feature/F3C-api-rest` |
| 4 | Integrador | F3-D Consola web, humo y evidencia (después de A, B y C) | `feature/F3D-consola-humo` |

Las sesiones 1, 2 y 3 trabajan **al mismo tiempo**. Sus PR se fusionan **en cualquier orden**. La sesión 4 empieza cuando las tres estén en `main`.

## Reglas para no crear conflictos (todas las sesiones)

1. **Parta de `main` actualizado**, con la base ya fusionada:
   ```bash
   git switch main && git pull
   git switch -c feature/F3A-algoritmos      # use la rama de SU sesión
   ```
2. **Toque solo los archivos de su sesión** (lista en cada sección). Si cree que necesita cambiar otro archivo, **no lo haga**: avise al grupo.
3. **No cambie las firmas congeladas:** nombres de clases, constructores, parámetros de `find`/`execute` y campos de los dataclasses. `tests/unit/test_f3_interfaces.py` lo vigila; si falla, el cambio está mal. No modifique esa prueba.
4. **Sin dependencias nuevas:** no toque `pyproject.toml` ni `uv.lock`. Dijkstra y BFS se implementan a mano (sin networkx).
5. **Documentación compartida:** edite solo **su fila** de la tabla "Estado de F3" en `docs/README.md` y solo **su sección** de "Evidencia" al final de `docs/features/F3-menor-costo.md`.
6. **Antes de abrir el PR**, actualice su rama y pase el harness:
   ```bash
   git fetch origin && git rebase origin/main
   make test
   ```
   Si el rebase marca conflicto en `docs/README.md`, conserve las filas de todos y cambie solo la suya.
7. **Commits** con Conventional Commits (p. ej. `feat(routing): implementar Dijkstra`). Abra el PR con la plantilla y **no haga merge** sin 1 revisión.

> **Windows sin `make`:** use los comandos de [07](../07-testing-y-harness.md). Si
> `docker compose run --build` falla con `failed to execute bake`, construya primero con
> `COMPOSE_BAKE=false docker compose -f docker-compose.test.yml build routing-tests` y luego ejecute
> `docker compose -f docker-compose.test.yml run --rm routing-tests`.

---

## Sesión 1 · Persona 1 — F3-A Algoritmos

**Construye:** el algoritmo de Dijkstra y el camino de menos tramos, en el dominio, sin I/O.

**Sus archivos** (en `services/routing-service/`):
- `src/routing_service/domain/cheapest_path/dijkstra.py`: cuerpo de `DijkstraPathFinder.find`.
- `src/routing_service/domain/cheapest_path/fewest_hops.py`: cuerpo de `BreadthFirstPathFinder.find`.
- `tests/unit/domain/cheapest_path/__init__.py` (vacío), `test_dijkstra.py` y `test_fewest_hops.py`: crear.
- `docs/05-algoritmos-dijkstra.md`: marcar `[x]` la checklist "Casos que deben probarse".

**Qué debe hacer `DijkstraPathFinder.find(graph, origin, destination, trace=False) -> PathResult`** (pseudocódigo en [05](../05-algoritmos-dijkstra.md)):
- `graph.require_node` para origen y destino (lanza `NodeNotFoundError`).
- Heap de `heapq` con tuplas `(costo, node_id)`, `dist`, `pred[nodo] = Arc usado` y un conjunto de fijados. Entradas obsoletas del heap se descartan; al fijar el destino se detiene.
- Antes de relajar cada arco: `validate_weight(arc.weight, arc.edge_id)` de `domain/graph.py` (lanza `InvalidWeightError` si el peso es ≤ 0, `inf` o `nan`).
- Si encuentra el destino: `PathResult(origin, destination, found=True, path=(nodos…), total_cost=..., trace=..., legs=(Arc…))`, con `legs[i]` de `path[i]` a `path[i+1]`. Si no: `found=False` y lo demás vacío.
- Origen = destino: `path=(origin,)`, `total_cost=0`, `legs=()`.
- **Traza** (solo si `trace=True`; si no, `()`), exactamente como la tabla de [05](../05-algoritmos-dijkstra.md#traza-b_norte--z_centro), 10 pasos para B_NORTE → Z_CENTRO:
  - `TraceStep(step, "pop", nodo, {"cost": c})`: cada nodo fijado abre un `step` nuevo (1, 2, 3…);
  - `TraceStep(step, "relax", vecino, {"cost": nuevo, "from": u, "edge_id": id})`, más `"previous": viejo` si ya tenía costo;
  - `TraceStep(step, "skip", vecino, {"cost": candidato, "best": vigente, "from": u})` si no mejora;
  - `TraceStep(step, "stale", nodo, {"cost": c})` para una entrada obsoleta (mismo `step` del último `pop`).
  - Los costos van como `float` (`0.0`, `5.0`).

**Qué debe hacer `BreadthFirstPathFinder.find`:** un BFS que guarda `pred` (el `Arc`), ignora los pesos y para al descubrir el destino. `total_cost` es la suma de los pesos de `legs`. Mismo formato de `PathResult`. Traza opcional: `TraceStep(0, "enqueue", origen, {"hops": 0})`, `TraceStep(k, "visit", nodo, {})` y `TraceStep(k, "enqueue", vecino, {"from": nodo})`.

**Pruebas mínimas** (use `tests/demo_network.py`): los 9 casos de la checklist de [05](../05-algoritmos-dijkstra.md#casos-que-deben-probarse-f3), más el desempate por `id` y una entrada `stale`. Para inyectar un peso inválido, agregue el arco a mano: `graph._adjacency["A"].append(Arc("E_BAD", "A", "B", 0))`. Objetivo: 100 % en sus dos archivos.

**Verificación:** `make test-routing`.

**Prompt para su agente (Claude Code / Codex):**
```text
Eres el agente del carril F3-A (Algoritmos) de ServicioCerca. Lee en este orden: AGENTS.md,
docs/README.md, docs/features/F3-menor-costo.md, docs/features/F3-sesiones.md (Sesión 1 y
"Reglas para no crear conflictos") y docs/05-algoritmos-dijkstra.md. Luego lee
services/routing-service/src/routing_service/domain/{graph,results,errors,strategies}.py,
domain/cheapest_path/{dijkstra,fewest_hops}.py, domain/coverage/bfs.py (estilo de referencia),
tests/demo_network.py y tests/unit/test_f3_interfaces.py.
Rama: git switch main && git pull && git switch -c feature/F3A-algoritmos
Implementa SOLO lo que dice la Sesión 1 (cuerpos de find, traza exacta y pruebas). Solo puedes
tocar los archivos de la Sesión 1. No cambies firmas, no agregues dependencias y no uses networkx.
Si algo es ambiguo o contradice la documentación, DETENTE y pregúntame.
Verifica con `make test-routing` y al final `make test`; pega la salida real (pasos ==> y cobertura).
Actualiza tu fila en docs/README.md y la sección "Evidencia > F3-A" de F3-menor-costo.md.
No hagas commit ni push sin mi autorización; cuando la dé, usa Conventional Commits.
```

---

## Sesión 2 · Persona 2 — F3-B Casos de uso

**Construye:** la lógica de aplicación que usa los algoritmos para responder las dos preguntas.

**Sus archivos** (en `services/routing-service/`):
- `src/routing_service/application/routes.py`: cuerpo de `FindCheapestRoute.execute` y funciones de apoyo.
- `src/routing_service/application/attention.py`: cuerpo de `FindBestAttention.execute` y funciones de apoyo.
- `tests/unit/application/test_routes.py` y `test_attention.py`: crear.

**Qué debe hacer `FindCheapestRoute.execute(origin, destination, trace=False) -> RouteReport`:**
1. `graph = self._gateway.load_graph()`.
2. Si el origen no existe: `OriginNotFoundError(f"El origen '{origin}' no existe.", node_id=origin)`. Después, si el destino no existe: `DestinationNotFoundError(f"El destino '{destination}' no existe.", node_id=destination)`. Origen y destino pueden ser cualquier nodo.
3. `cheapest = self._path_finder.find(graph, origin, destination, trace=trace)`.
4. Si no hay camino: `found=False`, `path=()`, `total_cost=None`, `hops=None`, `legs=()`, `fewest_hops=None` y el mensaje `f"No hay ruta de {origin} a {destination}: ningún camino de la red los conecta en ese sentido."`. **No** se llama al buscador de menos tramos.
5. Si hay camino: `shortest = self._fewest_hops_finder.find(graph, origin, destination)` (sin traza). `legs` = `Leg(arc.edge_id, arc.source, arc.target, arc.weight)` por cada arco de `cheapest.legs`, y `fewest_hops = FewestHops(shortest.path, shortest.hops, shortest.total_cost)`.
6. Mensajes, con minutos en formato `f"{valor:g} min"` y "1 tramo" / "N tramos":
   - mismo nodo: `"El origen y el destino son el mismo nodo (B_NORTE): costo 0 min."`;
   - caminos iguales: `"Ruta de menor costo: 20 min en 2 tramos (coincide con el camino de menos tramos)."`;
   - distintos: `"Ruta de menor costo: 15 min en 3 tramos (el camino de menos tramos cuesta 30 min)."`.
7. `trace` = `cheapest.trace` si `trace=True`; si no, `()`.

**Qué debe hacer `FindBestAttention.execute(zone, trace=False) -> AttentionReport`:**
1. Si la zona no existe **o no es `ZONE`**: `ZoneNotFoundError(f"La zona '{zone}' no existe.", node_id=zone)`.
2. Candidatas: bases (en orden de `id`) con al menos un técnico disponible (`node.available_technicians`). Ejecuta `self._path_finder.find(graph, base, zone, trace=trace)` desde cada una.
3. Ordena las que llegan por `(total_cost, hops, id de la base)`. La primera es `best` (`BestBase` con **solo** los técnicos disponibles) y el resto son `alternatives`.
4. Mensaje con éxito: `"Atender desde B_SUR (Marta): 20 min."`. Si hay varios técnicos, separados por `", "`.
5. Si ninguna candidata llega: `found=False`, `best=None`, `alternatives=()` y:
   - si alguna base **sin** técnicos disponibles sí llega: `"Z_FUENTE no se puede atender: solo es alcanzable desde bases sin técnicos disponibles (B_OESTE)."`;
   - si no: `"Z_ISLA no se puede atender: es inalcanzable desde toda base."`.
6. Traza (si `trace=True`): concatena la de cada candidata y agrega `"base": id` al `data` de cada paso.

**Pruebas mínimas:** con *fakes* de `PathFinder` y de `NetworkGateway` (como en `test_coverage.py`), para no depender de F3-A:
- orden de errores, los tres mensajes de ruta y "no hay ruta" sin llamar al de menos tramos;
- traza solo cuando se pide;
- los 4 ejemplos de [05](../05-algoritmos-dijkstra.md#mejor-alternativa-de-atención-attentionbest): Colina → B_SUR 20 con B_NORTE 25 de alternativa; Estación → B_SUR 15; Fuente y Isla con sus mensajes;
- desempates; "base pasada como zona" → `ZONE_NOT_FOUND`.

Para los ejemplos, el *fake* devuelve el `PathResult` esperado según el par (base, zona). Objetivo: 100 % en sus dos archivos.

**Verificación:** `make test-routing`.

**Prompt para su agente:**
```text
Eres el agente del carril F3-B (Casos de uso) de ServicioCerca. Lee en este orden: AGENTS.md,
docs/README.md, docs/features/F3-menor-costo.md, docs/features/F3-sesiones.md (Sesión 2 y
"Reglas para no crear conflictos"), docs/05-algoritmos-dijkstra.md y docs/03-api.md
(routing-service). Luego lee services/routing-service/src/routing_service/application/
{routes,attention,coverage,ports}.py, domain/{graph,results,errors,strategies}.py,
tests/unit/application/test_coverage.py (estilo de fakes), tests/demo_network.py y
tests/unit/test_f3_interfaces.py.
Rama: git switch main && git pull && git switch -c feature/F3B-casos-de-uso
Implementa SOLO lo de la Sesión 2: cuerpos de execute, mensajes EXACTOS y pruebas con fakes de
PathFinder (no dependas de Dijkstra real: lo hace otra persona en paralelo). Solo puedes tocar
los archivos de la Sesión 2. No cambies firmas ni dataclasses. Si algo es ambiguo, DETENTE y
pregúntame. Verifica con `make test-routing` y al final `make test`; pega la salida real.
Actualiza tu fila en docs/README.md y la sección "Evidencia > F3-B" de F3-menor-costo.md.
No hagas commit ni push sin mi autorización; cuando la dé, usa Conventional Commits.
```

---

## Sesión 3 · Persona 3 — F3-C API REST

**Construye:** los dos endpoints HTTP, la inyección de dependencias y el mapeo de errores.

**Sus archivos** (en `services/routing-service/`):
- Crear `src/routing_service/api/errors.py`: `STATUS_BY_CODE` (`ORIGIN_NOT_FOUND`, `DESTINATION_NOT_FOUND`, `ZONE_NOT_FOUND` → 404; `INVALID_ORIGIN`, `INVALID_WEIGHT` → 422) y `to_app_error(exc: DomainError) -> AppError` (400 si el código no figura).
- Crear `src/routing_service/api/trace.py`: `TraceStepOut` y `trace_out(...)`, movidos desde `api/coverage.py`.
- Crear `src/routing_service/api/routes.py`: `GET /api/v1/routes/cheapest`.
- Crear `src/routing_service/api/attention.py`: `GET /api/v1/attention/best`.
- `api/coverage.py`: usar `to_app_error` y `trace.py` (quitar su `_STATUS_BY_CODE` y `TraceStepOut` propios).
- `api/dependencies.py`: agregar `provide_path_finder` (→ `DijkstraPathFinder`), `provide_fewest_hops_finder` (→ `BreadthFirstPathFinder`), `provide_find_cheapest_route` y `provide_find_best_attention`.
- `main.py`: registrar los dos routers.
- `infrastructure/network_gateway.py`: en `_build_graph`, capturar también `NodeNotFoundError` y `DuplicateNodeError` → `NETWORK_UNAVAILABLE`. `InvalidWeightError` se sigue propagando.
- Pruebas: crear `tests/unit/api/test_routes_api.py` y `test_attention_api.py`; **agregar al final** de `test_coverage_api.py` (peso inválido → 422) y de `test_network_gateway.py` (red incoherente → 503).
- `docs/03-api.md`: solo cambiar ⏳ por ✅ en las dos filas de F3.

**Contrato:** exactamente el de [03-api.md](../03-api.md#get-apiv1routescheapestoriginb_nortedestinationz_centrotracetrue--f3):
- Parámetros con `Query(pattern=r"^[A-Z0-9_-]{1,32}$")` y `trace: bool = False`. La respuesta lleva `"trace": null` si no se pide.
- Roles `require_roles(Role.COORDINATOR, Role.OPERATOR)`: sin clave 401; `internal`, 403.
- En `legs`, los campos `source`/`target` del dataclass salen como `from`/`to`: `Field(serialization_alias="from")` (porque `from` es palabra reservada).
- `try: use_case.execute(...) except DomainError as exc: raise to_app_error(exc) from exc`.

**Pruebas mínimas** (como `test_coverage_api.py`): para no depender de A y B, reemplace el caso de uso con `app.dependency_overrides[provide_find_cheapest_route] = lambda: FakeUseCase(...)`, donde el *fake* devuelve un `RouteReport` / `AttentionReport` armado a mano o lanza un `DomainError`. Cubra:
- la respuesta completa con `from`/`to`, y `found=false` con 200;
- traza solo cuando se pide;
- 404 de `ORIGIN_NOT_FOUND`, `DESTINATION_NOT_FOUND` y `ZONE_NOT_FOUND`;
- 422 de `VALIDATION_ERROR` (sin reflejar la entrada) y de `INVALID_WEIGHT`;
- 503 de `NETWORK_UNAVAILABLE`, 401 y 403.

Objetivo: 100 % en sus archivos.

**Verificación:** `make test-routing`. Luego `make up` y abra <http://localhost:8002/docs>: deben aparecer los dos endpoints. Hasta que A y B estén en `main`, llamarlos de verdad responde `500`; es normal.

**Prompt para su agente:**
```text
Eres el agente del carril F3-C (API REST) de ServicioCerca. Lee en este orden: AGENTS.md,
docs/README.md, docs/features/F3-menor-costo.md, docs/features/F3-sesiones.md (Sesión 3 y
"Reglas para no crear conflictos"), docs/03-api.md (routing-service) y docs/06-seguridad.md.
Luego lee services/routing-service/src/routing_service/api/{coverage,dependencies,health}.py,
main.py, core/{errors,security}.py, infrastructure/network_gateway.py,
application/{routes,attention}.py (solo las firmas: las implementa otra persona en paralelo),
tests/unit/api/test_coverage_api.py, tests/unit/infrastructure/test_network_gateway.py y
tests/unit/test_f3_interfaces.py.
Rama: git switch main && git pull && git switch -c feature/F3C-api-rest
Implementa SOLO lo de la Sesión 3. Prueba los endpoints con casos de uso FALSOS vía
app.dependency_overrides (no dependas de Dijkstra ni de los casos de uso reales). Solo puedes
tocar los archivos de la Sesión 3; en los archivos de prueba existentes solo AGREGA al final.
Ningún error debe reflejar la entrada del cliente. Si algo contradice el contrato, DETENTE y
pregúntame. Verifica con `make test-routing` y al final `make test`; pega la salida real.
Actualiza tu fila en docs/README.md, las dos filas de F3 en docs/03-api.md y la sección
"Evidencia > F3-C" de F3-menor-costo.md. El PR lleva la etiqueta contract-change.
No hagas commit ni push sin mi autorización; cuando la dé, usa Conventional Commits.
```

---

## Sesión 4 · Integrador — F3-D Consola, humo y evidencia

**Empieza cuando A, B y C estén en `main`.** Construye la pestaña **Menor costo** de la consola web `services/web` ([ADR 0007](../adr/0007-consola-web-react-bff.md)) (ruta entre dos puntos y mejor base para una zona, con la ruta resaltada en ámbar en el mapa), `scripts/smoke_f3.sh` y el cierre de la documentación (`docs/10`, `F4`, `README.md`, tablas de estado y evidencia).

**Sus archivos:** `services/web/**` (rutas del BFF, tipos, pestaña y pruebas; la consola Streamlit está en retiro y no se toca), `scripts/smoke_f3.sh`, `docs/10-guia-prueba-manual.md`, `docs/features/F4-consola.md`, `README.md`, las tablas de estado finales y `docs/features/evidencia/F3/`.

**Verificación final:**
```bash
git switch main && git pull && git switch -c feature/F3D-consola-humo
make test
make reset && make up
sh scripts/smoke_f3.sh       # esperado: OK: smoke F3 en verde
```
