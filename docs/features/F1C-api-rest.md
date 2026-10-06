# F1-C · API REST de la red

- **Rama:** `feature/F1C-api-rest` · **Estado:** ⏳ Pendiente
- **Dueño:** _(nombre)_
- **Lea antes:** [F1 (general)](F1-red-cobertura.md), [03-api](../03-api.md#network-service-8001--feature-1) (**contrato**), [06-seguridad](../06-seguridad.md)

## Objetivo
Exponer los casos de uso de F1 como endpoints HTTP según el contrato:
- esquemas Pydantic de entrada y salida;
- autorización por rol;
- inyección de dependencias.

La API **no contiene reglas de negocio**: convierte JSON en entidades, llama al caso de uso y convierte el resultado otra vez en JSON. Los errores de dominio se propagan solos y `api/error_mapping.py` (ya hecho) los traduce.

## Archivos que puede modificar o crear (y solo estos)
- `src/network_service/api/schemas.py` (crear).
- `src/network_service/api/nodes.py`, `edges.py` y `network.py`: agregar endpoints al `router` que ya existe y que ya está registrado en `main.py`.
- `src/network_service/api/dependencies.py`: agregar proveedores. **No** modifique `get_repository` ni `_repository_singleton`.
- `tests/unit/api/test_nodes_api.py`, `test_edges_api.py` y `test_network_api.py` (crear).
- `docs/03-api.md`: solo cambiar ⏳ por ✅ en los endpoints que implemente.
- `docs/features/F1C-api-rest.md` (este archivo) y **su fila** en `docs/README.md`.

Todo lo anterior está bajo `services/network-service/`, salvo la documentación. No toque `main.py`, `error_mapping.py`, `core/**` ni los casos de uso (su implementación es de F1-A; usted solo los **importa**).

## Esquemas (`api/schemas.py`)
Todos con `model_config = ConfigDict(extra="forbid")`. Los campos desconocidos producen `VALIDATION_ERROR`.

| Esquema | Campos |
|---|---|
| `TechnicianIn` / `TechnicianOut` | `id: str`, `name: str`, `available: bool = True` |
| `NodeIn` | `id: str`, `type: NodeType`, `name: str`, `technicians: list[TechnicianIn] = []` (máx. 100) |
| `NodeOut` | igual que `NodeIn`, con `technicians: list[TechnicianOut]` (siempre presente; `[]` en zonas) |
| `EdgeIn` / `EdgeOut` | `id: str`, `source: str`, `target: str`, `weight: float`, `bidirectional: bool = True` |
| `NetworkOut` | `nodes: list[NodeOut]`, `edges: list[EdgeOut]` |
| `NetworkImportIn` | `nodes: list[NodeIn]` (máx. 1000), `edges: list[EdgeIn]` (máx. 5000), `replace: bool = False` |
| `ImportSummaryOut` | `nodes: int`, `edges: int` |

Reglas:
- **No** ponga en Pydantic las reglas de negocio: formato del id, rango del peso o largo del nombre. Las valida el dominio (F1-A) para devolver los códigos específicos del contrato, como `INVALID_WEIGHT`.
- En Pydantic solo van **tipos y forma**: campos requeridos, tipos y el enum `NodeType`. Agregue además límites anti-abuso **amplios** en los strings (`max_length=256`).
- Conversión a entidades: `NodeIn.to_domain() -> Node` (técnicos como tupla), `EdgeIn.to_domain() -> Edge`. Conversión desde entidades: `NodeOut.from_domain(node)`, `EdgeOut.from_domain(edge)`, `NetworkOut.from_domain(network)`, `ImportSummaryOut.from_domain(summary)`.

## Proveedores (`api/dependencies.py`)
Uno por caso de uso, con este nombre y esta forma exacta (las pruebas los sobrescriben):
```python
def provide_register_node(
    repository: Annotated[NetworkRepository, Depends(get_repository)],
) -> RegisterNode:
    return RegisterNode(repository)
```
`provide_register_node`, `provide_get_node`, `provide_list_nodes`, `provide_delete_node`, `provide_register_edge`, `provide_list_edges`, `provide_delete_edge`, `provide_get_network` y `provide_import_network`.

## Endpoints

| Método y ruta | Roles (`require_roles`) | Caso de uso | Éxito |
|---|---|---|---|
| `POST /api/v1/nodes` | coordinator | `RegisterNode` | `201` `NodeOut` |
| `GET /api/v1/nodes` | coordinator, operator | `ListNodes` | `200` `list[NodeOut]` |
| `GET /api/v1/nodes/{node_id}` | coordinator, operator | `GetNode` | `200` `NodeOut` |
| `DELETE /api/v1/nodes/{node_id}` | coordinator | `DeleteNode` | `204`, sin cuerpo |
| `POST /api/v1/edges` | coordinator | `RegisterEdge` | `201` `EdgeOut` |
| `GET /api/v1/edges` | coordinator, operator | `ListEdges` | `200` `list[EdgeOut]` |
| `DELETE /api/v1/edges/{edge_id}` | coordinator | `DeleteEdge` | `204`, sin cuerpo |
| `GET /api/v1/network` | coordinator, operator, **internal** | `GetNetwork` | `200` `NetworkOut` |
| `POST /api/v1/network/import` | coordinator | `ImportNetwork` | `201` `ImportSummaryOut` |

- Autorización: `dependencies=[Depends(require_roles(Role.COORDINATOR, ...))]` en cada endpoint (`core/security.py`).
- Los parámetros de ruta `{node_id}` y `{edge_id}` **no** se validan con regex: un id con formato inválido simplemente no existe y produce `NODE_NOT_FOUND` / `EDGE_NOT_FOUND`.
- Cada endpoint declara `summary` en español y `response_model`, para que Swagger quede legible.
- **No** capture `DomainError` en los routers.

## Pruebas obligatorias
Use `create_app()` con `app.dependency_overrides`. **Sobrescriba los proveedores con fakes** (clases mínimas con `execute`), de modo que sus pruebas no dependan de la implementación de F1-A. Use los fixtures de headers por rol de `tests/conftest.py`.

Para **cada endpoint**:
- [ ] Éxito: código HTTP y cuerpo exacto. En `DELETE`, `204` con cuerpo vacío.
- [ ] Conversión correcta: el fake **captura** el argumento recibido (`Node`/`Edge` con técnicos en tupla, `replace`, ids de ruta).
- [ ] Sin `X-API-Key`: `401 UNAUTHENTICATED`. Con un rol no permitido: `403 FORBIDDEN` (operator en escrituras; internal en todo salvo `GET /network`).

Además:
- [ ] Forma inválida: campo faltante, campo extra, `type` inválido y `weight` no numérico dan `422 VALIDATION_ERROR`, y la respuesta no refleja el valor enviado.
- [ ] Peso negativo **llega al caso de uso** (Pydantic no lo rechaza). El fake lanza `InvalidWeightError` y la respuesta es `422 INVALID_WEIGHT`.
- [ ] Propagación de errores de dominio: el fake lanza `NodeNotFoundError`/`DuplicateIdError`/`NodeInUseError` y la respuesta trae el status y `{code, message, details}` correctos.
- [ ] `POST /network/import` acepta el contenido de `seed/red_demo.json`: cópielo en un fixture de la prueba, porque la carpeta `seed/` no está dentro del contexto Docker del servicio.
- [ ] Swagger: `/openapi.json` contiene las 9 rutas.

## Definition of Done
- [ ] `make test-network` y `make test` en verde.
- [ ] Endpoints marcados ✅ en `docs/03-api.md`. El estado está actualizado en este archivo y en `docs/README.md`.
- [ ] PR con la plantilla completa.

## Evidencia
_Pegar el resumen de `make test-network` y una captura de Swagger (`http://localhost:8001/docs`)._
