# 05 · Alternativa de menor costo con Dijkstra (Feature 3)

## Elección respaldada por las condiciones de los pesos

El brief pide que la elección se apoye en las **condiciones de los pesos** y no en la popularidad del algoritmo:

| Condición de pesos | Algoritmo adecuado |
|---|---|
| Todos iguales (o sin peso) | BFS: el menor costo coincide con el menor número de tramos |
| **Todos positivos** (nuestro caso: minutos > 0) | **Dijkstra**, O((V + E) log V) con heap |
| Puede haber negativos, sin ciclos negativos | Bellman-Ford, O(V·E) |
| Ciclos negativos | No existe un "menor costo" bien definido |

Nuestros pesos son **tiempos de traslado**, físicamente **> 0**, y se validan en tres capas:

1. **API** (network-service): `0 < weight ≤ 1440`; si no, se responde `INVALID_WEIGHT`.
2. **Base de datos**: `CHECK (weight > 0)`.
3. **Algoritmo**: Dijkstra verifica cada arco y lanza `InvalidWeightError` ante un peso ≤ 0 o no finito, porque un peso negativo **invalida** su invariante.

¿Por qué un peso negativo rompe Dijkstra? Dijkstra **fija** un nodo cuando lo saca del heap, suponiendo que ningún camino posterior puede abaratarlo. Con un arco negativo, un camino descubierto después sí podría hacerlo, y el resultado sería incorrecto. Por eso se rechaza de forma explícita y no se "intenta igual".

## Cómo se mantienen los costos candidatos y se reconstruye el camino

```
Dijkstra(G, origen, destino):
    validar origen/destino existen
    dist ← {origen: 0};  pred ← {}; heap ← [(0, origen)]; fijados ← ∅
    mientras heap no vacío:
        (d, u) ← heappop(heap)                    # traza: pop u (d)
        si u ∈ fijados: continuar                 # entrada obsoleta del heap ("lazy deletion")
        fijados.add(u)
        si u == destino: romper                   # salida temprana
        para cada arco (u→v, w) en G.neighbors(u):
            si w ≤ 0 o no finito: error INVALID_WEIGHT
            si d + w < dist.get(v, ∞):            # relajación
                dist[v] ← d + w; pred[v] ← (u, arco)   # traza: relax v
                heappush(heap, (dist[v], v))
    si destino ∉ dist: retornar found=false
    camino ← seguir pred desde destino hasta origen y luego invertir
```

- **Costos candidatos:** `dist` guarda el mejor costo conocido. El heap puede tener entradas viejas, que se descartan al sacarlas si el nodo ya está fijado.
- **Reconstrucción:** `pred[v]` guarda el nodo anterior y el arco usado. Así se obtienen `path` y `legs` con el `edge_id` de cada tramo.
- **Desempates deterministas:** vecinos ordenados y heap con tuplas `(costo, node_id)`. Así las trazas y las pruebas son estables.

## Caso donde menos tramos ≠ menor costo (requisito del brief)

En la red demo, de `B_NORTE` a `Z_CENTRO`:

| Camino | Tramos | Costo |
|---|---|---|
| B_NORTE → Z_CENTRO (directo, E01) | **1** | 30 min |
| B_NORTE → Z_ALAMEDA → Z_BOSQUE → Z_CENTRO | 3 | **15 min** |

BFS, por número de tramos, elegiría el camino directo. Dijkstra elige el de 15 min. La API devuelve los dos (`path` y `fewest_hops`) y la consola los muestra juntos, para que el operador vea la diferencia.

### Traza (B_NORTE → Z_CENTRO)

| Paso | Pop (costo) | Relajaciones | dist después |
|---|---|---|---|
| 1 | B_NORTE (0) | Z_ALAMEDA = 5, Z_CENTRO = 30 | {B_NORTE:0, Z_ALAMEDA:5, Z_CENTRO:30} |
| 2 | Z_ALAMEDA (5) | B_NORTE: 10 ≥ 0, no mejora · Z_BOSQUE = 10 | {…, Z_BOSQUE:10} |
| 3 | Z_BOSQUE (10) | Z_ALAMEDA: no mejora · **Z_CENTRO: 15 < 30, se actualiza** (pred = Z_BOSQUE) | {…, Z_CENTRO:15} |
| 4 | Z_CENTRO (15) | destino fijado, se detiene | — |

El camino se reconstruye con `pred`: Z_CENTRO ← Z_BOSQUE ← Z_ALAMEDA ← B_NORTE. Costo total: **15**.
La entrada `(30, Z_CENTRO)` queda obsoleta en el heap y nunca se procesa.

## Mejor alternativa de atención (`/attention/best`)

1. Las candidatas son las bases con al menos un técnico `available=true`.
2. Se ejecuta Dijkstra desde cada candidata hasta la zona.
   - Es O(B·(V + E) log V), aceptable con pocas bases.
   - La alternativa sería un Dijkstra único sobre el grafo invertido desde la zona. Queda documentada como optimización futura.
3. Se elige la de menor `total_cost`. En caso de empate gana menos tramos y luego el `id` de la base. El resto va en `alternatives`.

Ejemplos con la red demo:

| Zona | Resultado |
|---|---|
| `Z_COLINA` | B_SUR, 20 min, gana sobre B_NORTE con 25 |
| `Z_ESTACION` | B_SUR, 15 min |
| `Z_FUENTE` | `found=false`: solo la alcanza B_OESTE, que no tiene técnicos disponibles |
| `Z_ISLA` | `found=false`: inalcanzable desde toda base |

## Casos que deben probarse (F3)

- [ ] Ruta posible con camino y costo exactos (B_NORTE → Z_CENTRO = 15).
- [ ] Contraejemplo de tramos frente a costo: `fewest_hops.hops < hops` y `fewest_hops.cost > total_cost`.
- [ ] Ruta imposible por red desconectada (B_NORTE → Z_FUENTE): `found=false`, sin error.
- [ ] Arista de un solo sentido: hay ruta de B_SUR a Z_ESTACION, pero no en sentido inverso.
- [ ] Peso inválido (0, negativo, `inf`, `nan`) inyectado en un `Graph` de prueba: `InvalidWeightError` o `INVALID_WEIGHT`.
- [ ] Origen o destino inexistente: `ORIGIN_NOT_FOUND` / `DESTINATION_NOT_FOUND`.
- [ ] Origen igual a destino: camino `[origen]`, costo 0.
- [ ] La traza coincide con la tabla de este documento.
- [ ] `/attention/best`: los cuatro ejemplos de la tabla anterior.
