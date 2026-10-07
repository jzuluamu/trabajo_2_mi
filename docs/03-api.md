# 03 · Contrato de API (congelado en Fase 0)

> Este contrato permite que las 4 personas trabajen en paralelo. **Todo cambio** se hace con un PR
> etiquetado `contract-change`, aprobado por los dueños de los servicios afectados, y actualizando
> este archivo **antes** o **junto con** el código.
> Swagger vivo: <http://localhost:8001/docs> y <http://localhost:8002/docs>.

Leyenda: ✅ implementado · ⏳ pendiente (fase indicada)

## Convenciones

- Prefijo `/api/v1`. JSON UTF-8. Los identificadores siguen `^[A-Z0-9_-]{1,32}$`.
- **Espacios de nombres de ids:** son independientes para nodos, conexiones y técnicos. Un nodo y una conexión pueden compartir id, pero dos nodos no. Los técnicos son únicos en toda la red.
- **Orden de errores** (cuando hay varios problemas, se informa el primero):
  - nodos: formato → `DUPLICATE_ID` de nodo → `DUPLICATE_ID` de técnico;
  - conexiones: formato (`VALIDATION_ERROR`, `SELF_LOOP`, `INVALID_WEIGHT`) → `DUPLICATE_ID` → `NODE_NOT_FOUND` → `DUPLICATE_EDGE`.

  Detalle en [F1-A](features/F1A-dominio-casos-de-uso.md).
- **Ids en la ruta** (`/nodes/{id}`): no se valida su formato. Un id inexistente o mal formado responde `NODE_NOT_FOUND` / `EDGE_NOT_FOUND`. Si el id **no** cumple el formato, la respuesta no lo refleja: `message` genérico ("El nodo solicitado no existe.") y `details` vacío (F1-D).
- **Autenticación:** encabezado `X-API-Key`. Roles: `coordinator`, `operator` e `internal` ([06-seguridad.md](06-seguridad.md)).
- **Errores**, siempre con la misma forma:

```json
{ "code": "ZONE_NOT_FOUND", "message": "La zona 'Z_X' no existe.", "details": { "node_id": "Z_X" } }
```

### Catálogo de códigos de error

| HTTP | `code` | Cuándo |
|---|---|---|
| 401 | `UNAUTHENTICATED` | Falta `X-API-Key` o no es válida |
| 403 | `FORBIDDEN` | El rol no tiene permiso para la acción |
| 404 | `NODE_NOT_FOUND` | El nodo referenciado no existe (CRUD, aristas) |
| 404 | `EDGE_NOT_FOUND` | La conexión no existe |
| 404 | `ORIGIN_NOT_FOUND` | El origen de la consulta no existe |
| 404 | `ZONE_NOT_FOUND` / `DESTINATION_NOT_FOUND` | La zona o el destino de la consulta no existe |
| 409 | `DUPLICATE_ID` | Ya existe un nodo, una conexión o un técnico con ese `id` |
| 409 | `DUPLICATE_EDGE` | Ya existe la misma conexión entre esos nodos (ver [02](02-modelo-de-grafo.md#duplicados)) |
| 409 | `NODE_IN_USE` | Se intenta borrar un nodo que tiene conexiones |
| 422 | `VALIDATION_ERROR` | Formato inválido (id, campos faltantes, tipos) |
| 422 | `INVALID_WEIGHT` | Peso ≤ 0, no finito o > 1440. **Se usa este código y no `VALIDATION_ERROR`** |
| 422 | `SELF_LOOP` | `source == target` |
| 422 | `INVALID_ORIGIN` | El origen de una cobertura no es una `BASE` |
| 503 | `NETWORK_UNAVAILABLE` | routing-service no pudo obtener la red de network-service |
| 500 | `INTERNAL_ERROR` | Error inesperado, sin detalles internos |

**Regla:** que no exista un camino **no es un error**. Es una respuesta válida de negocio, con `200`, `found=false` o `covered=false` y un `message` legible.

---

## network-service (`:8001`) — Feature 1

| Método y ruta | Roles | Estado |
|---|---|---|
| `GET /health` | público | ✅ |
| `GET /api/v1/auth/whoami` | todos | ✅ |
| `POST /api/v1/nodes` | coordinator | ✅ F1-C |
| `GET /api/v1/nodes` · `GET /api/v1/nodes/{id}` | coordinator, operator | ✅ F1-C |
| `DELETE /api/v1/nodes/{id}` | coordinator | ✅ F1-C |
| `POST /api/v1/edges` | coordinator | ✅ F1-C |
| `GET /api/v1/edges` | coordinator, operator | ✅ F1-C |
| `DELETE /api/v1/edges/{id}` | coordinator | ✅ F1-C |
| `GET /api/v1/network` | coordinator, operator, internal | ✅ F1-C |
| `POST /api/v1/network/import` | coordinator | ✅ F1-C |

### `GET /api/v1/auth/whoami` ✅

`200 {"role": "operator"}`. Lo usa la consola para iniciar sesión.

### `POST /api/v1/nodes`

```json
{ "id": "B_NORTE", "type": "BASE", "name": "Base Norte",
  "technicians": [ { "id": "T01", "name": "Ana", "available": true } ] }
```

- `type` es `BASE` o `ZONE`. `technicians` es opcional y **solo** se acepta en `BASE`; por defecto es `[]`.
- `name` tiene entre 1 y 80 caracteres.
- Responde `201` con el nodo creado.
- Errores posibles: `DUPLICATE_ID` y `VALIDATION_ERROR`.

### `DELETE /api/v1/nodes/{id}`

Responde `204`. Errores posibles: `NODE_NOT_FOUND` y `NODE_IN_USE` (con `details.edge_ids`, las conexiones que lo usan).

### `POST /api/v1/edges`

```json
{ "id": "E01", "source": "B_NORTE", "target": "Z_CENTRO", "weight": 30, "bidirectional": true }
```

- `weight` debe ser un **número JSON**. `true` o `"30"` dan `VALIDATION_ERROR` (F1-D); un número fuera de rango da `INVALID_WEIGHT`.
- Responde `201` con la conexión.
- Errores posibles: `NODE_NOT_FOUND`, `DUPLICATE_ID`, `DUPLICATE_EDGE`, `INVALID_WEIGHT` y `SELF_LOOP`.

### `DELETE /api/v1/edges/{id}`

Responde `204`. Error posible: `EDGE_NOT_FOUND`.

### `GET /api/v1/network`

```json
{
  "nodes": [ { "id": "B_NORTE", "type": "BASE", "name": "Base Norte",
               "technicians": [ { "id": "T01", "name": "Ana", "available": true } ] },
             { "id": "Z_CENTRO", "type": "ZONE", "name": "Centro", "technicians": [] } ],
  "edges": [ { "id": "E01", "source": "B_NORTE", "target": "Z_CENTRO", "weight": 30, "bidirectional": true } ]
}
```

- Listas ordenadas por `id`.
- Es la fuente única que consume routing-service (rol `internal`) y la consola (para visualizar).

### `POST /api/v1/network/import`

- Cuerpo: `{"nodes": [...], "edges": [...], "replace": true}`. `replace` es opcional y por defecto vale `false`, así que **agrega** a la red existente.
- Es **atómico**: o se importa todo o nada.
- Con `replace=true` borra la red previa.
- Responde `201 {"nodes": <n>, "edges": <m>}`.
- Aplica las mismas validaciones que los endpoints individuales. Los errores incluyen en `details` `section` (`"nodes"` o `"edges"`) e `index` del elemento que falló.
- Lo usa la consola (cargar `seed/red_demo.json`) y las pruebas de aceptación.

---

## routing-service (`:8002`) — Features 2 y 3

| Método y ruta | Roles | Estado |
|---|---|---|
| `GET /health` | público | ✅ |
| `GET /api/v1/coverage` | coordinator, operator | ⏳ F2 |
| `GET /api/v1/routes/cheapest` | coordinator, operator | ⏳ F3 |
| `GET /api/v1/attention/best` | coordinator, operator | ⏳ F3 |

Todos aceptan `trace=true` para incluir la traza paso a paso (`TraceStep`: `step`, `action`, `node`, `data`).

### `GET /api/v1/coverage?base=B_NORTE[&zone=Z_CENTRO][&trace=true]` — F2

```json
{
  "base": "B_NORTE",
  "reachable": [ { "node_id": "Z_ALAMEDA", "type": "ZONE", "hops": 1 },
                 { "node_id": "Z_CENTRO",  "type": "ZONE", "hops": 1 } ],
  "unreachable_zones": [ "Z_FUENTE", "Z_ISLA" ],
  "zone": { "id": "Z_CENTRO", "covered": true, "hops": 1,
            "message": "Z_CENTRO está cubierta desde B_NORTE (1 tramo)." },
  "trace": null
}
```

- `reachable` excluye el origen y se ordena por `(hops, node_id)`.
- `zone` es `null` si no se envió `zone`. Si la zona existe pero no es alcanzable, la respuesta es `covered=false`, `hops=null` y un `message` que explica que no hay conexión.
- Errores posibles:
  - `ORIGIN_NOT_FOUND`: la base no existe.
  - `INVALID_ORIGIN`: el origen no es una base.
  - `ZONE_NOT_FOUND`: la zona no existe.
  - `NETWORK_UNAVAILABLE`: no se pudo obtener la red.

### `GET /api/v1/routes/cheapest?origin=B_NORTE&destination=Z_CENTRO[&trace=true]` — F3

Respuesta cuando existe camino:

```json
{
  "found": true, "origin": "B_NORTE", "destination": "Z_CENTRO",
  "path": [ "B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO" ],
  "total_cost": 15.0, "hops": 3,
  "legs": [ { "edge_id": "E02", "from": "B_NORTE", "to": "Z_ALAMEDA", "weight": 5.0 }, "..." ],
  "fewest_hops": { "path": [ "B_NORTE", "Z_CENTRO" ], "hops": 1, "cost": 30.0 },
  "message": "Ruta de menor costo: 15 min en 3 tramos (el camino de menos tramos cuesta 30 min).",
  "trace": null
}
```

- Cuando no existe camino, la respuesta es `found=false`, `path=[]`, `total_cost=null`, `hops=null`, `legs=[]` y `fewest_hops=null`, con un `message` legible.
- Errores posibles:
  - `ORIGIN_NOT_FOUND` y `DESTINATION_NOT_FOUND`.
  - `INVALID_WEIGHT`: defensa en profundidad, si la red trae un peso inválido.
  - `NETWORK_UNAVAILABLE`.

### `GET /api/v1/attention/best?zone=Z_COLINA[&trace=true]` — F3

Elige, entre las bases con **al menos un técnico disponible**, la de menor costo hasta la zona.

```json
{
  "zone": "Z_COLINA", "found": true,
  "best": { "base": "B_SUR", "technicians": [ { "id": "T03", "name": "Marta" } ],
            "path": [ "B_SUR", "Z_DELICIAS", "Z_COLINA" ], "total_cost": 20.0, "hops": 2 },
  "alternatives": [ { "base": "B_NORTE", "total_cost": 25.0, "hops": 4 } ],
  "message": "Atender desde B_SUR (Marta): 20 min.",
  "trace": null
}
```

- `alternatives` lista las demás bases con técnico disponible que alcanzan la zona, ordenadas por costo.
- Si ninguna base con técnico disponible alcanza la zona, la respuesta es `found=false`, `best=null` y un `message` que distingue dos casos:
  - "inalcanzable desde toda base";
  - "solo alcanzable desde bases sin técnicos disponibles".
- Errores posibles: `ZONE_NOT_FOUND` y `NETWORK_UNAVAILABLE`.
