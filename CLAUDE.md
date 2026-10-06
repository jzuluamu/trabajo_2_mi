# CLAUDE.md

@AGENTS.md

## Reglas adicionales para Claude

- **Siempre**, antes de escribir código o documentación, lea `docs/README.md` y los documentos relacionados que indica AGENTS.md §1. No se salte este paso aunque el cambio parezca trivial.
- Si su cambio altera comportamiento, API, modelo o configuración, actualice la documentación en el mismo cambio (AGENTS.md §2) y menciónelo en su resumen final.
- Su criterio de "OK" es `make test` en verde. Para iterar rápido puede usar un solo servicio: `make test-network`, `make test-routing` o `make test-console`. Antes de declarar la tarea terminada, ejecute `make test` completo y reporte el resultado real.
- Al terminar una fase o feature, indique al humano **qué probar** (pasos de `docs/10-guia-prueba-manual.md`) y **qué cambios necesita en `.env`**, si los hay.
- Comandos útiles: `make help`, `make up`, `make down`, `make logs`, `make lock` (tras cambiar dependencias).
