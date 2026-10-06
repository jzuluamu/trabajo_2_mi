# F2 · Consulta de cobertura (BFS)

- **Servicio:** `routing-service` (`domain/coverage/`) · **Dueño:** Persona 2 · **Estado:** ⏳ Pendiente (Fase 1)
- **Lea antes:** [04-algoritmos-bfs](../04-algoritmos-bfs.md), [02-modelo-de-grafo](../02-modelo-de-grafo.md), [03-api](../03-api.md#get-apiv1coveragebaseb_nortezonez_centrotracetrue--f2)

## Valor de negocio
El operador sabe si una solicitud está dentro de una cobertura posible y qué zonas pueden alcanzarse desde una base.

## Criterios de aceptación
- [ ] Recibe la base (y opcionalmente una zona) y lista el alcance con `hops` mínimos.
- [ ] BFS **implementado por el equipo** (`BreadthFirstReachability`, que implementa `ReachabilityStrategy`), justificado en [04](../04-algoritmos-bfs.md).
- [ ] Resultado legible ante:
  - una red desconectada (`unreachable_zones`);
  - un origen inexistente (`ORIGIN_NOT_FOUND`) o que no es base (`INVALID_ORIGIN`);
  - una zona inexistente (`ZONE_NOT_FOUND`);
  - una zona sin conexión (`covered=false` con `message`).
- [ ] `trace=true` devuelve la traza, que coincide con el ejemplo pequeño de [04](../04-algoritmos-bfs.md).
- [ ] Pruebas unitarias con todos los casos de la checklist de [04](../04-algoritmos-bfs.md).

## Diseño sugerido
- `domain/coverage/bfs.py`: algoritmo puro.
- `application/coverage.py`: caso de uso `CheckCoverage(gateway: NetworkGateway, strategy: ReachabilityStrategy)`.
- `api/coverage.py`: router y esquemas. Traduce `DomainError` a los códigos del contrato.

## Evidencia (Fase 3)
_Pendiente._
