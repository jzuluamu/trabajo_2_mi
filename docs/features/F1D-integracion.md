# F1-D · Integración, interfaz mínima y cierre de F1

- **Rama:** `feature/F1D-integracion` · **Estado:** ✅ Terminada (con evidencia en [F1](F1-red-cobertura.md#evidencia))
- **Dueño:** integrador _(nombre)_
- **Lea antes:** [F1 (general)](F1-red-cobertura.md), [F1A](F1A-dominio-casos-de-uso.md), [F1B](F1B-persistencia.md), [F1C](F1C-api-rest.md), [03-api](../03-api.md), [ADR 0005](../adr/0005-consola-streamlit.md)

## Objetivo
Unir los tres carriles, probar F1 de punta a punta, agregar la **interfaz mínima** que exige el brief y cerrar la documentación con evidencia.

## Trabajo

1. **Prueba punta a punta de la API** en `services/network-service/tests/unit/api/test_f1_end_to_end.py`. Usa `create_app()` con los proveedores **reales** y solo sobrescribe `get_repository` con un `InMemoryNetworkRepository` nuevo por prueba. Cubre:
   - [x] importar la red demo, y `GET /network` devuelve 11 nodos y 9 conexiones ordenados;
   - [x] un ciclo completo con nodos y conexiones: crear, listar, consultar y borrar;
   - [x] todos los códigos de error de F1 del contrato, a través de HTTP: `VALIDATION_ERROR`, `INVALID_WEIGHT`, `SELF_LOOP`, `NODE_NOT_FOUND`, `EDGE_NOT_FOUND`, `DUPLICATE_ID`, `DUPLICATE_EDGE`, `NODE_IN_USE`, `401` y `403`;
   - [x] importación atómica: un lote con error no deja nada guardado.
2. **Prueba de humo contra Docker**: el script `scripts/smoke_f1.sh` en la raíz usa `curl` y lee las claves desde `.env`. Hace lo siguiente sobre la demo levantada:
   - [x] importa `seed/red_demo.json`;
   - [x] lee la red;
   - [x] provoca `INVALID_WEIGHT`;
   - [x] reinicia `network-service` y comprueba que los datos **persisten** en PostgreSQL.

   Debe terminar con código ≠ 0 si algo falla. Agregue el target `make smoke-f1`.
3. **Interfaz mínima** en `services/console`, siguiendo el patrón existente: clientes en `clients/`, componentes en `components/` y lógica fuera de `app.py`.
   - [x] `NetworkClient`: `get_network()`, `create_node(...)`, `create_edge(...)`, `delete_node(id)`, `delete_edge(id)`, `import_network(payload)`. Usan la API key de la sesión.
   - [x] Página o sección **Red** (ambos roles): tablas de nodos (con técnicos) y de conexiones (peso y sentido), con un botón "Actualizar".
   - [x] Solo para **coordinador**: formularios para crear una base o zona (con técnicos) y una conexión; botones para borrar; y "Cargar red demo" con `st.file_uploader` (JSON) que llama a `/network/import`.
   - [x] Los errores se muestran con `message` legible (por ejemplo, el peso negativo muestra el mensaje de `INVALID_WEIGHT`).
   - [x] Pruebas con `AppTest` y `httpx.MockTransport`. La cobertura de la consola debe seguir ≥ 85 %.
4. **Cierre de documentación**:
   - [x] Estado ✅ de F1 en `docs/README.md` y en `README.md`.
   - [x] Sección de F1 en `docs/10-guia-prueba-manual.md`.
   - [x] Evidencia (capturas de la consola y salidas de `smoke-f1`) en `docs/features/F1-red-cobertura.md`.

## Ajustes hechos al integrar
La revisión de A, B y C encontró dos detalles, corregidos aquí con sus pruebas:
- **Peso no numérico aceptado:** `"weight": true` se guardaba como 1.0 y `"30"` como 30.0, porque Pydantic convierte tipos por defecto. Ahora `EdgeIn.weight` es estricto y esos valores dan `VALIDATION_ERROR` ([F1-C](F1C-api-rest.md)).
- **Id de ruta reflejado:** `GET /nodes/<script>` devolvía `"El nodo '<script>' no existe."`. Ahora un id mal formado responde con un mensaje genérico y `details` vacío ([F1-A](F1A-dominio-casos-de-uso.md), [06](../06-seguridad.md), [03](../03-api.md)).

Decisiones de la interfaz:
- Los técnicos se escriben una línea por técnico (`ID; Nombre; sí/no`): `st.data_editor` no es manipulable desde `AppTest`.
- `st.file_uploader` tampoco lo es: la lectura del JSON (`parse_network_file`) y la importación (`import_file`) se prueban por separado.
- El mensaje de éxito se muestra sobre las pestañas para que el coordinador lo vea desde "Configurar red".
- `tests/fixtures/red_demo.json` es una copia de `seed/red_demo.json`, porque la imagen de pruebas solo ve la carpeta del servicio. `make smoke-f1` usa el original.

## Definition of Done
- [x] `make test` y `make smoke-f1` en verde con una base limpia (verificado en un proyecto Compose aislado con volumen nuevo).
- [ ] Recorrido manual de la guía 10, sección F1, sin errores (lo hace una persona del equipo).
- [ ] PR con la plantilla completa (pendiente de abrir).
