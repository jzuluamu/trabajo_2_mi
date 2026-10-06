# F3 · Alternativa de atención de menor costo (Dijkstra)

- **Servicio:** `routing-service` (`domain/cheapest_path/`) · **Dueño:** Persona 3 · **Estado:** ⏳ Pendiente (Fase 1)
- **Lea antes:** [05-algoritmos-dijkstra](../05-algoritmos-dijkstra.md), [02-modelo-de-grafo](../02-modelo-de-grafo.md), [03-api](../03-api.md#get-apiv1routescheapestoriginb_nortedestinationz_centrotracetrue--f3)

## Valor de negocio
El operador consulta una ruta o alternativa de llegada con el menor tiempo estimado.

## Criterios de aceptación
- [ ] `/routes/cheapest` recibe origen y destino, y devuelve `path`, `legs` y `total_cost` cuando existe un camino.
- [ ] Rechaza de forma explícita los pesos que invalidan Dijkstra (`INVALID_WEIGHT`), con defensa en profundidad.
- [ ] Explica un caso donde menos tramos no es menor costo: campo `fewest_hops` y el ejemplo B_NORTE → Z_CENTRO.
- [ ] Prueba casos de ruta posible e imposible (`found=false`, sin error).
- [ ] `/attention/best` elige la base con técnico disponible de menor costo y distingue las zonas inalcanzables de las alcanzables solo por bases sin técnicos.
- [ ] Dijkstra **implementado por el equipo** (`DijkstraPathFinder`, que implementa `PathFinder`) con `heapq` y reconstrucción por `pred`.
- [ ] `trace=true` coincide con la traza de [05](../05-algoritmos-dijkstra.md).

## Diseño sugerido
- `domain/cheapest_path/dijkstra.py`: algoritmo puro.
- `application/routes.py`: casos de uso `FindCheapestRoute` y `FindBestAttention`. Para `fewest_hops` se reutiliza `ReachabilityStrategy` o un BFS de camino.
- `api/routes.py` y `api/attention.py`: routers.

## Evidencia (Fase 3)
_Pendiente._
