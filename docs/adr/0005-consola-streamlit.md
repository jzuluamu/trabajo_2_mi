# 0005 · Consola en Streamlit

- **Estado:** Aceptado
- **Fecha:** 2026-10-05

## Contexto
Feature 4 exige una consola que integre configuración, cobertura y ruta, muestre la red y destaque el resultado. El equipo trabaja en Python.

## Decisión
- **Streamlit** para la interfaz y **pyvis** para el grafo interactivo, con la ruta y la cobertura resaltadas. Cómo se embebe de forma segura: [ADR 0006](0006-grafo-pyvis-embebido-seguro.md).
- La consola solo consume las APIs mediante clientes HTTP (`console/clients/`). La lógica de la UI vive en módulos importables y se prueba con `streamlit.testing.v1.AppTest`.

## Alternativas consideradas
- **React + Vite + TypeScript + Cytoscape.js:** ofrece mejor experiencia de usuario, pero agrega una segunda toolchain (npm, vitest), CORS o un gateway nginx y una curva de aprendizaje para el equipo. Se descarta para el MVP.
- **Plantillas Jinja en FastAPI:** requeriría construir toda la interactividad a mano.

## Consecuencias
- Un solo lenguaje y un solo harness para todo el proyecto.
- El modelo de re-ejecución de Streamlit exige mantener el estado en `st.session_state` y poner las llamadas a la API en clientes con timeout.
- Si se necesitara una SPA, el contrato HTTP permite reemplazar la consola sin tocar los servicios.
