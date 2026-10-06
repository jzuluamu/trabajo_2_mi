# 0003 · Modelo de grafo: técnicos como atributo, grafo dirigido con aristas bidireccionales

- **Estado:** Aceptado
- **Fecha:** 2026-10-05

## Contexto
El brief pide especificar qué representa cada nodo y arista, comparar la disponibilidad como atributo frente a como relación, y justificar si una conexión se recorre en ambos sentidos.

## Decisión
- Los nodos son `BASE` y `ZONE`. Los técnicos (con `available`) son **atributo** de la base.
- Las aristas son trayectos con `weight` = minutos (> 0) y `bidirectional` (por defecto `true`).
- Internamente el grafo es **dirigido**: una arista bidireccional genera dos arcos.

## Alternativas consideradas
- **Técnico como nodo o relación:** mezcla dos semánticas de arista ("trabaja en" y "se traslada por"), lo que rompe el significado del costo total de Dijkstra. Se descarta.
- **Grafo no dirigido puro:** no permite modelar vías de un solo sentido ni tiempos asimétricos.
- **Grafo dirigido puro, obligando a registrar dos aristas:** duplica la carga del coordinador en el caso más común.

## Consecuencias
- Hay una sola semántica de peso, de modo que BFS (alcance) y Dijkstra (costo) operan sobre el mismo `Graph`.
- La disponibilidad no altera el grafo; solo filtra las bases candidatas en `/attention/best`.
- Detalle en `docs/02-modelo-de-grafo.md`.
