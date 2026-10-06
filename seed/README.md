# Datos semilla

`red_demo.json` es una red sintética con el formato de `POST /api/v1/network/import` ([contrato](../docs/03-api.md)).
Está diseñada para cubrir los casos que pide el brief. Su diagrama y su explicación están en [docs/02-modelo-de-grafo.md](../docs/02-modelo-de-grafo.md#red-de-demostración-seedred_demojson).

| Caso | Dónde |
|---|---|
| Menos tramos ≠ menor costo | B_NORTE → Z_CENTRO (directo 30 contra 15 por Alameda y Bosque) |
| Trayecto de un solo sentido | E08 Z_DELICIAS → Z_ESTACION |
| Red desconectada | Componente B_OESTE–Z_FUENTE y zona aislada Z_ISLA |
| Zona alcanzable pero no atendible | Z_FUENTE (B_OESTE no tiene técnicos disponibles) |

Si cambia este archivo, actualice las trazas y tablas de `docs/04` y `docs/05`.
