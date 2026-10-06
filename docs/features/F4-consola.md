# F4 · Consola de operación demostrable

- **Servicio:** `console` · **Dueño:** Persona 4 · **Estado:** 🟡 Base lista (Fase 0: inicio de sesión por rol + estado de servicios)
- **Lea antes:** [ADR 0005](../adr/0005-consola-streamlit.md), [03-api](../03-api.md), [10-guia-prueba-manual](../10-guia-prueba-manual.md)

## Valor de negocio
El equipo de atención consulta la cobertura y la alternativa de servicio sin interpretar estructuras internas.

## Hecho en Fase 0
- [x] Inicio de sesión con API key: el rol se obtiene de `/auth/whoami` y la clave `internal` se rechaza.
- [x] Panel de estado de los servicios, con mensaje legible si un servicio está caído.
- [x] Clientes HTTP con traducción de errores del contrato (`ApiClientError`).

## Criterios de aceptación (Fases 1 a 3)
- [ ] **Coordinador:** formularios para registrar bases (con técnicos), zonas y conexiones; botón para cargar la red demo (`/network/import`); mensajes de validación legibles.
- [ ] **Operador:** consulta de cobertura (base y zona opcional), ruta de menor costo (origen y destino) y mejor atención (zona).
- [ ] **Visualización** (pyvis):
  - bases y zonas diferenciadas;
  - aristas con peso y dirección;
  - cobertura resaltada (nodos alcanzados y no alcanzados);
  - ruta resaltada, y el camino de menos tramos en un estilo distinto.
- [ ] Explicación en lenguaje natural del resultado (`message`) y traza opcional en un desplegable.
- [ ] Aceptación de: éxito, zona inexistente, red desconectada y peso inválido.
- [ ] Incorporar el **cambio de requisito docente** (Fase 4, por definir).
- [ ] Evidencia completa de la feature (capturas por escenario).

## Cambio de requisito docente
_Por definir. Registrar aquí el requisito, el ADR asociado y su impacto cuando se conozca._

## Evidencia (Fase 3)
_Pendiente._
