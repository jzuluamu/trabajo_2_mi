# F1-D · Integración, interfaz mínima y cierre de F1

- **Rama:** `feature/F1D-integracion` · **Estado:** ⏳ Pendiente; empieza cuando F1-A, F1-B y F1-C estén fusionados en `main`
- **Dueño:** integrador _(nombre)_
- **Lea antes:** [F1 (general)](F1-red-cobertura.md), [F1A](F1A-dominio-casos-de-uso.md), [F1B](F1B-persistencia.md), [F1C](F1C-api-rest.md), [03-api](../03-api.md), [ADR 0005](../adr/0005-consola-streamlit.md)

## Objetivo
Unir los tres carriles, probar F1 de punta a punta, agregar la **interfaz mínima** que exige el brief y cerrar la documentación con evidencia.

## Trabajo

1. **Prueba punta a punta de la API** en `services/network-service/tests/unit/api/test_f1_end_to_end.py`. Usa `create_app()` con los proveedores **reales** y solo sobrescribe `get_repository` con un `InMemoryNetworkRepository` nuevo por prueba. Cubre:
   - [ ] importar la red demo, y `GET /network` devuelve 11 nodos y 9 conexiones ordenados;
   - [ ] un ciclo completo con nodos y conexiones: crear, listar, consultar y borrar;
   - [ ] todos los códigos de error de F1 del contrato, a través de HTTP: `VALIDATION_ERROR`, `INVALID_WEIGHT`, `SELF_LOOP`, `NODE_NOT_FOUND`, `EDGE_NOT_FOUND`, `DUPLICATE_ID`, `DUPLICATE_EDGE`, `NODE_IN_USE`, `401` y `403`;
   - [ ] importación atómica: un lote con error no deja nada guardado.
2. **Prueba de humo contra Docker**: el script `scripts/smoke_f1.sh` en la raíz usa `curl` y lee las claves desde `.env`. Hace lo siguiente sobre la demo levantada:
   - [ ] importa `seed/red_demo.json`;
   - [ ] lee la red;
   - [ ] provoca `INVALID_WEIGHT`;
   - [ ] reinicia `network-service` y comprueba que los datos **persisten** en PostgreSQL.

   Debe terminar con código ≠ 0 si algo falla. Agregue el target `make smoke-f1`.
3. **Interfaz mínima** en `services/console`, siguiendo el patrón existente: clientes en `clients/`, componentes en `components/` y lógica fuera de `app.py`.
   - [ ] `NetworkClient`: `get_network()`, `create_node(...)`, `create_edge(...)`, `delete_node(id)`, `delete_edge(id)`, `import_network(payload)`. Usan la API key de la sesión.
   - [ ] Página o sección **Red** (ambos roles): tablas de nodos (con técnicos) y de conexiones (peso y sentido), con un botón "Actualizar".
   - [ ] Solo para **coordinador**: formularios para crear una base o zona (con técnicos) y una conexión; botones para borrar; y "Cargar red demo" con `st.file_uploader` (JSON) que llama a `/network/import`.
   - [ ] Los errores se muestran con `message` legible (por ejemplo, el peso negativo muestra el mensaje de `INVALID_WEIGHT`).
   - [ ] Pruebas con `AppTest` y `httpx.MockTransport`. La cobertura de la consola debe seguir ≥ 85 %.
4. **Cierre de documentación**:
   - [ ] Estado ✅ de F1 en `docs/README.md` y en `README.md`.
   - [ ] Sección de F1 en `docs/10-guia-prueba-manual.md`.
   - [ ] Evidencia (capturas de la consola y salidas de `smoke-f1`) en `docs/features/F1-red-cobertura.md`.

## Definition of Done
- [ ] `make test` y `make smoke-f1` en verde con una base limpia (`make reset && make up`).
- [ ] Recorrido manual de la guía 10, sección F1, sin errores.
- [ ] PR con la plantilla completa.
