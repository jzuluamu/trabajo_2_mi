# F1 · Red de cobertura

- **Servicio:** `network-service` · **Dueño:** Persona 1 · **Estado:** ⏳ Pendiente (Fase 1)
- **Lea antes:** [02-modelo-de-grafo](../02-modelo-de-grafo.md), [03-api](../03-api.md#network-service-8001--feature-1), [06-seguridad](../06-seguridad.md)

## Valor de negocio
El coordinador configura zonas y conexiones operativas asociadas a bases y técnicos.

## Historias
- Como **coordinador**, registro bases (con técnicos), zonas y conexiones para que el sistema conozca la red.
- Como **operador**, consulto la red para entender qué existe, sin poder modificarla.

## Criterios de aceptación
- [ ] Se crean, listan, consultan y eliminan nodos y conexiones según el contrato.
- [ ] Identificadores validados con `^[A-Z0-9_-]{1,32}$`. Si no cumplen, se responde `VALIDATION_ERROR`.
- [ ] Duplicados rechazados:
  - `DUPLICATE_ID` (nodo, conexión o técnico);
  - `DUPLICATE_EDGE` (mismo par o, si es bidireccional, el par inverso).
- [ ] Pesos: `0 < weight ≤ 1440`. Si no cumplen, se responde `INVALID_WEIGHT` (no `VALIDATION_ERROR`). Además existe `CHECK` en la base de datos.
- [ ] `source == target` responde `SELF_LOOP`. Un nodo inexistente responde `NODE_NOT_FOUND`. Borrar un nodo con conexiones responde `NODE_IN_USE`.
- [ ] Solo se aceptan técnicos en nodos `BASE`.
- [ ] `GET /api/v1/network` devuelve la red completa ordenada. Acceden los roles coordinator, operator e internal.
- [ ] `POST /api/v1/network/import` es atómico (todo o nada) y acepta `seed/red_demo.json`.
- [ ] Permisos: operator recibe 403 al escribir; sin clave, 401.
- [ ] Migraciones Alembic aplicadas al arrancar el contenedor.
- [ ] Justificación documentada de la bidireccionalidad ([02](../02-modelo-de-grafo.md)).

## Diseño sugerido (SOLID)
- `domain/`: entidades `Node`, `Edge`, `Technician` y reglas de duplicado.
- `application/`: puertos `NetworkReader` y `NetworkWriter` (ISP); casos de uso `RegisterNode`, `RegisterEdge`, `ImportNetwork`, etc.
- `infrastructure/`: repositorios SQLAlchemy y uno en memoria para las pruebas (LSP).

## Evidencia (Fase 3)
_Pendiente: capturas de Swagger y respuestas de cada error._
