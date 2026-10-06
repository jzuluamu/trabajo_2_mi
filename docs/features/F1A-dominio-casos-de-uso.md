# F1-A · Dominio y casos de uso

- **Rama:** `feature/F1A-dominio-casos-de-uso` · **Estado:** ✅ Lista (pendiente de revisión)
- **Dueño:** Daniela Zuluaga
- **Lea antes:** [F1 (general)](F1-red-cobertura.md), [02-modelo-de-grafo](../02-modelo-de-grafo.md), [03-api](../03-api.md)

## Objetivo
Implementar las **reglas de negocio** de la red y los **9 casos de uso** que usará la API (F1-C). Todo es Python puro, sin I/O: el repositorio llega inyectado.

## Archivos que puede modificar o crear (y solo estos)
- `services/network-service/src/network_service/domain/rules.py`: reemplazar cada `raise NotImplementedError` por la implementación.
- `services/network-service/src/network_service/application/use_cases.py`: ídem.
- `services/network-service/tests/unit/domain/test_rules.py` (crear).
- `services/network-service/tests/unit/application/test_use_cases.py` (crear). Puede dividirlo en varios `test_*.py` dentro de esa carpeta.
- `docs/features/F1A-dominio-casos-de-uso.md` (este archivo: estado y evidencia) y **su fila** en `docs/README.md`.

**No modifique** las firmas: `tests/unit/test_frozen_interfaces.py` falla si lo hace. Tampoco toque `models.py`, `errors.py`, `ports.py` ni `memory_repository.py`. Si necesita una función auxiliar, créela como privada (`_nombre`) dentro de los mismos archivos.

## Interfaces que usa (ya existen, congeladas)
- Entidades `Node`, `Edge`, `Technician`, `NodeType`, `Network`, `ImportSummary`, y las constantes `ID_PATTERN`, `NAME_MAX_LENGTH = 80` y `WEIGHT_MAX_MINUTES = 1440.0`, en `domain/models.py`.
- Errores `InvalidFieldError`, `InvalidWeightError`, `SelfLoopError`, `NodeNotFoundError`, `EdgeNotFoundError`, `DuplicateIdError`, `DuplicateEdgeError` y `NodeInUseError`, en `domain/errors.py`. Se construyen así: `Error("mensaje", clave=valor, ...)`, donde los `kwargs` pasan a `details`.
- Puertos `NetworkReader` y `NetworkRepository`, en `application/ports.py`.
- En las pruebas: `InMemoryNetworkRepository` (`infrastructure/memory_repository.py`).

## Especificación de `domain/rules.py`

| Función | Regla | Error (mensaje exacto · `details`) |
|---|---|---|
| `validate_identifier(value, field)` | `re.fullmatch(ID_PATTERN, value)` | `InvalidFieldError("El campo '{field}' debe tener entre 1 y 32 caracteres: A-Z, 0-9, '_' o '-'.")` · `{"field": field}` |
| `validate_name(value, field)` | `1 <= len(value.strip()) <= 80` | `InvalidFieldError("El campo '{field}' debe tener entre 1 y 80 caracteres.")` · `{"field": field}` |
| `validate_weight(weight, edge_id)` | `math.isfinite(weight) and 0 < weight <= 1440` | `InvalidWeightError("El peso de la conexión '{edge_id}' debe ser mayor que 0 y menor o igual a 1440 minutos.")` · `{"edge_id": edge_id}` |
| `validate_node(node)` | Orden: (1) id; (2) name; (3) zona con técnicos; (4) cada técnico `i`: id y name con field `technicians[i].id` / `technicians[i].name`; (5) id de técnico repetido dentro del nodo | (3) `InvalidFieldError("Solo las bases pueden tener técnicos.")` · `{"field": "technicians"}`. (5) `DuplicateIdError("El técnico '{tid}' está repetido en el nodo '{node.id}'.")` · `{"technician_id": tid}` |
| `validate_edge(edge)` | Orden: (1) id, source, target con `validate_identifier` (fields `"id"`, `"source"`, `"target"`); (2) `source == target`; (3) `validate_weight` | (2) `SelfLoopError("La conexión '{edge.id}' no puede unir un nodo consigo mismo.")` · `{"edge_id": edge.id}` |
| `edges_conflict(new, existing) -> bool` | `True` si hay el mismo `(source, target)`, o si hay el par inverso y `new.bidirectional or existing.bidirectional` | — |

Notas:
- **Nunca** incluya en el mensaje ni en `details` el valor inválido recibido (seguridad, [06](../06-seguridad.md)). Los ids ya validados sí pueden aparecer.
- `validate_identifier` es sensible a mayúsculas: `"b1"` es inválido.

## Especificación de `application/use_cases.py`

`repo` = `self._repository`. Los errores van **en el orden indicado**; las pruebas verifican el orden.

| Caso de uso | Pasos |
|---|---|
| `RegisterNode.execute(node) -> Node` | 1) `validate_node(node)`. 2) Si `repo.get_node(node.id)` existe: `DuplicateIdError("Ya existe un nodo con id '{id}'.", node_id=id)`. 3) Por cada técnico, si `repo.technician_exists(t.id)`: `DuplicateIdError("Ya existe un técnico con id '{tid}'.", technician_id=tid)`. 4) `repo.add_node(node)` y retornar `node`. |
| `RegisterEdge.execute(edge) -> Edge` | 1) `validate_edge(edge)`. 2) Si `repo.get_edge(edge.id)` existe: `DuplicateIdError("Ya existe una conexión con id '{id}'.", edge_id=id)`. 3) Si no existe `source`, y luego si no existe `target`: `NodeNotFoundError("El nodo '{nid}' no existe.", node_id=nid)`. 4) Para cada `e` en `repo.list_edges()`, si `edges_conflict(edge, e)`: `DuplicateEdgeError("Ya existe una conexión entre '{e.source}' y '{e.target}' ({e.id}).", edge_id=e.id)`. 5) `repo.add_edge(edge)` y retornar `edge`. |
| `GetNode.execute(node_id) -> Node` | Retornar el nodo, o `NodeNotFoundError("El nodo '{node_id}' no existe.", node_id=node_id)`. |
| `ListNodes.execute() -> list[Node]` | `repo.list_nodes()`, que ya viene ordenado por id. |
| `ListEdges.execute() -> list[Edge]` | `repo.list_edges()`, que ya viene ordenado por id. |
| `DeleteNode.execute(node_id) -> None` | 1) Si no existe: `NodeNotFoundError`, igual que `GetNode`. 2) `uses = sorted(e.id for e in repo.list_edges() if node_id in (e.source, e.target))`; si hay alguno: `NodeInUseError("El nodo '{node_id}' tiene conexiones; elimínelas primero.", node_id=node_id, edge_ids=uses)`. 3) `repo.delete_node(node_id)`. |
| `DeleteEdge.execute(edge_id) -> None` | 1) Si no existe: `EdgeNotFoundError("La conexión '{edge_id}' no existe.", edge_id=edge_id)`. 2) `repo.delete_edge(edge_id)`. |
| `GetNetwork.execute() -> Network` | `Network(nodes=tuple(repo.list_nodes()), edges=tuple(repo.list_edges()))`. |
| `ImportNetwork.execute(nodes, edges, *, replace) -> ImportSummary` | Ver el detalle debajo. |

### `ImportNetwork` (atómico)
1. Prepare un repositorio de trabajo `InMemoryNetworkRepository()`. Si `replace` es `False`, cárguelo con el estado actual mediante `scratch.save_network(repo.list_nodes(), repo.list_edges(), replace=True)`. Si es `True`, déjelo vacío.
2. Para cada `i, node in enumerate(nodes)`, ejecute `RegisterNode(scratch).execute(node)`. Para cada `i, edge in enumerate(edges)`, ejecute `RegisterEdge(scratch).execute(edge)`. Así se reutilizan las mismas reglas y el mismo orden de errores (DRY).
3. Si alguno lanza `DomainError`, agregue `error.details["section"] = "nodes"` o `"edges"` y `error.details["index"] = i`, y **relance el mismo error**. **No** se escribe nada en `repo`.
4. Si todo es válido: `repo.save_network(nodes, edges, replace=replace)` y retornar `ImportSummary(nodes=len(nodes), edges=len(edges))`.

Importar `InMemoryNetworkRepository` en `application/` es una excepción aceptada y documentada: se usa como estructura de validación en memoria, no como persistencia.

## Pruebas obligatorias (mínimo)
Use la red demo ([02](../02-modelo-de-grafo.md#red-de-demostración-seedred_demojson)) o grafos pequeños. Siga el patrón AAA, un comportamiento por prueba, y verifique `code` y `details`, no solo el tipo.

**`tests/unit/domain/test_rules.py`**
- [ ] Identificadores válidos (`B1`, `Z_CENTRO`, `A-1`, 32 caracteres). Inválidos: vacío, 33 caracteres, minúsculas, espacio, acento y `Z.1`. En los inválidos, `details == {"field": ...}` y el mensaje no contiene el valor.
- [ ] Nombre: vacío, solo espacios y 81 caracteres son inválidos; 80 caracteres es válido.
- [ ] Peso: `0`, `-1`, `1440.01`, `inf` y `nan` son inválidos; `0.5` y `1440` son válidos.
- [ ] `validate_node`: zona con técnicos; técnico con id inválido (field `technicians[0].id`); técnico repetido en el nodo; base válida con técnicos; orden (un id inválido se reporta antes que un nombre inválido).
- [ ] `validate_edge`: lazo (`SELF_LOOP`); orden (un id inválido antes que el lazo, y el lazo antes que el peso).
- [ ] `edges_conflict`: mismo par; inverso con `bi`/`bi`, `bi`/no y no/`bi` es `True`; inverso con no/no es `False`; pares distintos son `False`.

**`tests/unit/application/test_use_cases.py`** (con `InMemoryNetworkRepository`)
- [ ] `RegisterNode`: éxito (queda guardado); `DUPLICATE_ID` de nodo; `DUPLICATE_ID` de técnico existente en otra base; validación delegada (zona con técnicos).
- [ ] `RegisterEdge`: éxito; `DUPLICATE_ID`; `NODE_NOT_FOUND` de source y de target (con `details.node_id` correcto); `DUPLICATE_EDGE` mismo par e inverso bidireccional; un único sentido inverso con ambos no bidireccionales **sí** se permite; `INVALID_WEIGHT`; `SELF_LOOP`.
- [ ] `GetNode`/`DeleteNode`/`DeleteEdge`: los `*_NOT_FOUND`; `NODE_IN_USE` con `edge_ids` ordenados; borrado exitoso.
- [ ] `ListNodes`/`ListEdges`/`GetNetwork`: orden por id.
- [ ] `ImportNetwork`:
  - importa `seed/red_demo.json` (construya las entidades en la prueba) y da `ImportSummary(11, 9)`;
  - `replace=True` reemplaza;
  - `replace=False` agrega;
  - un error en `edges[2]` da `details` con `section="edges"` e `index=2`, y el repositorio queda **intacto**;
  - un nodo duplicado dentro del lote da `section="nodes"` e `index=1`;
  - con `replace=False`, una conexión que referencia un nodo existente es válida.

## Definition of Done
- [x] `make test-network` en verde y luego `make test` en verde (cobertura ≥ 85 %; apunte a 100 % en `rules.py` y `use_cases.py`).
- [x] `tests/unit/test_frozen_interfaces.py` sin cambios y en verde.
- [x] Estado actualizado en este archivo y en `docs/README.md`.
- [ ] PR con la plantilla completa.

## Evidencia

`docker compose -f docker-compose.test.yml run --rm --build network-tests` (equivalente a
`make test-network`; Docker no traía `make` en esta terminal, así que se usó el comando
documentado en [07-testing-y-harness.md](../07-testing-y-harness.md)):

```
==> ruff (lint)
All checks passed!
==> ruff (formato)
48 files already formatted
==> mypy (tipos)
Success: no issues found in 47 source files
==> bandit (seguridad)
==> pip-audit (CVEs)
No known vulnerabilities found
==> pytest
tests/integration/test_migrations.py .                                   [  0%]
tests/unit/api/test_dependencies.py ..                                   [  2%]
tests/unit/api/test_error_mapping.py ..........                          [ 10%]
tests/unit/application/test_use_cases.py ..............................  [ 33%]
tests/unit/domain/test_rules.py .....................................    [ 62%]
tests/unit/infrastructure/test_memory_repository.py ................     [ 74%]
tests/unit/test_config.py .....                                          [ 78%]
tests/unit/test_errors.py ....                                           [ 81%]
tests/unit/test_frozen_interfaces.py ...............                     [ 93%]
tests/unit/test_health.py ..                                             [ 94%]
tests/unit/test_security.py .......                                      [100%]

Name                                                      Stmts   Miss Branch BrPart  Cover
-----------------------------------------------------------------------------------------------
src/network_service/application/use_cases.py                 97      0     30      0   100%
src/network_service/domain/rules.py                          39      0     20      0   100%
TOTAL                                                       416      0     78      0   100%
Required test coverage of 85% reached. Total coverage: 100.00%
129 passed in 2.55s
```

Esta vez corrió también `tests/integration/test_migrations.py` (Postgres real vía
`docker-compose.test.yml`), ya no se salta. `tests/unit/test_frozen_interfaces.py` quedó sin
cambios y en verde (15 pruebas).

`make test` completo (`network-tests` arriba + `routing-tests` + `console-tests`, corridos con
`docker compose -f docker-compose.test.yml run --rm --build <servicio>`):

- **routing-service:** ruff, mypy y bandit en verde; `pytest` → 27 passed, cobertura 100 %.
- **console:** ruff, mypy y bandit en verde; `pytest` → 11 passed, cobertura 98.65 % (≥ 85 %
  requerido).

Los 3 servicios terminan en verde: Definition of Done de F1-A cumplida.
