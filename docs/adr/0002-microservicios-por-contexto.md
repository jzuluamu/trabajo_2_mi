# 0002 · Microservicios por contexto de negocio

- **Estado:** Aceptado
- **Fecha:** 2026-10-05

## Contexto
Se pide una arquitectura de microservicios separados por rol, que soporte el trabajo de 4 personas.

## Decisión
Se usan tres servicios de aplicación, más la base de datos:
- `network-service`: configura la red y es el único dueño de los datos.
- `routing-service`: calcula sobre la red, sin estado. Contiene BFS y Dijkstra en módulos separados.
- `console`: la interfaz.

La comunicación es solo HTTP, según el contrato `docs/03-api.md`. No se comparten librerías: cada servicio tiene su propio `core/`.

## Alternativas consideradas
- **Un servicio por algoritmo** (coverage-service y path-service): ambos necesitan el mismo grafo. Se duplicaría la carga de la red, el `Graph`, la seguridad y la infraestructura, y no hay escalado independiente que lo justifique. Se considera sobreingeniería.
- **Monolito modular:** sería lo más simple, pero no cumple el requisito de microservicios.
- **API gateway (nginx/Traefik):** innecesario, porque la consola Streamlit llama a las APIs desde el servidor y no hay CORS. Podría agregarse si se cambia a un SPA.
- **Librería compartida (`common/`):** acopla las versiones de los servicios. Se acepta duplicar ~100 líneas de `core/`.

## Consecuencias
- routing-service pide la red en cada consulta. Es simple y siempre consistente, adecuado al volumen del MVP.
- Los cambios de contrato requieren coordinación (PR `contract-change`).
