# 04 · Cobertura con BFS (Feature 2)

## ¿Qué significa "cubrir"?

El brief pide decidir entre tres opciones: existencia de camino, número de pasos o costo. Definimos:

> **Z está cubierta por B ⇔ existe un camino dirigido de B a Z en la red.**

Es una pregunta de **alcance**: no optimiza costo, porque eso es F3. Como dato adicional se informa el **número mínimo de tramos** (`hops`), útil para el operador y gratuito con BFS.

## ¿Por qué BFS y no DFS?

| Criterio | BFS | DFS |
|---|---|---|
| ¿Decide el alcance? | Sí | Sí |
| ¿Entrega el mínimo número de tramos? | **Sí**, porque visita por niveles | No: el primer camino que encuentra puede ser largo |
| Implementación | Iterativa, con una cola `deque` | Recursiva: puede agotar la pila en redes grandes, o iterativa con pila explícita |
| Complejidad | O(V + E) | O(V + E) |
| Traza para explicar | Natural: "nivel 1, nivel 2…" | Menos intuitiva para un operador |

Ambos resuelven el alcance con la misma complejidad. **BFS se elige** porque además da `hops` mínimos sin costo extra y produce una traza por niveles fácil de explicar en la demo.

## Algoritmo (contrato en `routing_service/domain/strategies.py`)

```
BFS(G, origen):
    si origen ∉ G: error ORIGIN_NOT_FOUND
    hops ← {origen: 0};  cola ← [origen]
    mientras cola no vacía:
        u ← cola.popleft()                       # traza: visit u
        para cada arco (u→v) en G.neighbors(u):  # vecinos ordenados → traza determinista
            si v ∉ hops:
                hops[v] ← hops[u] + 1            # traza: enqueue v
                cola.append(v)
    retornar ReachabilityResult(origen, hops, traza)
```

Notas:
- Se marca `v` como visitado **al encolarlo**, no al sacarlo, para no encolarlo dos veces.
- Los arcos ya están expandidos: una conexión bidireccional son dos arcos ([02](02-modelo-de-grafo.md)).
- Los pesos se **ignoran**, porque BFS responde alcance. La validez de los pesos es problema de F3.

## Traza de un ejemplo pequeño (red demo, origen `B_NORTE`)

Vecinos (ordenados):
- `B_NORTE` → `Z_ALAMEDA`, `Z_CENTRO`
- `Z_ALAMEDA` → `B_NORTE`, `Z_BOSQUE`
- `Z_BOSQUE` → `Z_ALAMEDA`, `Z_CENTRO`
- `Z_CENTRO` → `B_NORTE`, `Z_BOSQUE`, `Z_COLINA`
- `Z_COLINA` → `Z_CENTRO`, `Z_DELICIAS`
- `Z_DELICIAS` → `B_SUR`, `Z_COLINA`, `Z_ESTACION` (este último es de un solo sentido)

| Paso | Visita | Encola (hops) | Cola después |
|---|---|---|---|
| 0 | — | `B_NORTE` (0) | [B_NORTE] |
| 1 | B_NORTE | Z_ALAMEDA (1), Z_CENTRO (1) | [Z_ALAMEDA, Z_CENTRO] |
| 2 | Z_ALAMEDA | Z_BOSQUE (2) | [Z_CENTRO, Z_BOSQUE] |
| 3 | Z_CENTRO | Z_COLINA (2) | [Z_BOSQUE, Z_COLINA] |
| 4 | Z_BOSQUE | — | [Z_COLINA] |
| 5 | Z_COLINA | Z_DELICIAS (3) | [Z_DELICIAS] |
| 6 | Z_DELICIAS | B_SUR (4), Z_ESTACION (4) | [B_SUR, Z_ESTACION] |
| 7 | B_SUR | — | [Z_ESTACION] |
| 8 | Z_ESTACION | — (no tiene arcos salientes) | [] |

Resultado:
- **Cubiertas** desde `B_NORTE`: Z_ALAMEDA, Z_CENTRO, Z_BOSQUE, Z_COLINA, Z_DELICIAS y Z_ESTACION.
- **No cubiertas:** `Z_FUENTE`, que está en otra componente, y `Z_ISLA`, que no tiene conexiones. Para ellas la API responde `covered=false` con un mensaje, no un error.

## Casos que deben probarse (F2)

- [ ] Alcance correcto y `hops` mínimos en la red demo (tabla anterior).
- [ ] Red desconectada: las zonas de otra componente aparecen en `unreachable_zones`.
- [ ] Zona aislada, sin aristas: `covered=false`.
- [ ] Arista de un solo sentido: desde `Z_ESTACION` no se vuelve a `Z_DELICIAS`.
- [ ] Origen inexistente: `ORIGIN_NOT_FOUND`. Origen de tipo `ZONE`: `INVALID_ORIGIN`. Zona inexistente: `ZONE_NOT_FOUND`.
- [ ] La traza coincide paso a paso con la tabla de este documento.
- [ ] Ciclos (Z_ALAMEDA–Z_BOSQUE–Z_CENTRO–B_NORTE): BFS termina y no repite nodos.
