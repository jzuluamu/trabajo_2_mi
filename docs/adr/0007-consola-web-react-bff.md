# 0007 · Consola web en React con un BFF que guarda la API key

- **Estado:** Aceptado
- **Fecha:** 2026-10-28
- **Reemplaza a:** [0005](0005-consola-streamlit.md) y [0006](0006-grafo-pyvis-embebido-seguro.md) cuando la consola web alcance paridad. Mientras tanto, conviven.

## Contexto
La consola Streamlit ([ADR 0005](0005-consola-streamlit.md)) cumplió para F1 y F2, pero topó con límites de UX que el equipo quiere superar:
- Streamlit vuelve a ejecutar la página completa en cada interacción, con parpadeos y pérdida del estado visual.
- El mapa vive en un iframe de un solo sentido ([ADR 0006](0006-grafo-pyvis-embebido-seguro.md)): un clic en un nodo no puede abrir su ficha, y la cobertura no se pudo resaltar en el mapa.
- El layout es rígido: no hay paneles laterales fijos, modo oscuro ni un diseño móvil cuidado.

ADR 0005 ya preveía que el contrato HTTP permitía reemplazar la consola sin tocar los servicios. Lo delicado es la seguridad: todos los endpoints exigen `X-API-Key` ([06](../06-seguridad.md)). En Streamlit, la clave vive en la sesión del servidor; en una SPA, por defecto, viviría en el navegador.

## Decisión
Un servicio nuevo, `services/web`, con una sola toolchain (Node 24 LTS, npm):

- **SPA:** React 19 + Vite + TypeScript estricto.
  - **Tailwind CSS v4 + shadcn/ui (Radix):** tokens semánticos, tema claro y oscuro, y accesibilidad de teclado y ARIA ya resuelta.
  - **TanStack Query:** caché, estados de carga y error, y vuelta al inicio de sesión ante un 401.
  - **Cytoscape.js:** mapa interactivo. El clic en un nodo devuelve su id a React, y la cobertura se resalta por tramos en el propio mapa.
- **BFF en Hono** (mismo contenedor, mismo origen):
  - `POST /bff/session` valida la clave con `/auth/whoami` y la guarda **en memoria del servidor**. El navegador recibe solo una cookie `HttpOnly; SameSite=Strict` con un id aleatorio de 256 bits.
  - `/bff/api/{network|routing}/<ruta>` reenvía a `/api/v1/<ruta>` con la `X-API-Key` de la sesión. Solo admite las rutas del contrato ([03](../03-api.md)) en una **lista blanca**, y los ids en la ruta deben tener la forma `[A-Za-z0-9_-]`.
  - Los métodos que modifican exigen el encabezado `X-ServicioCerca: 1` (CSRF), además de la cookie `SameSite=Strict`.
  - CSP estricta: `script-src 'self'`, sin scripts en línea y `frame-ancestors 'none'`.
  - La autorización por rol la sigue decidiendo cada servicio. El BFF no la duplica.
- **Harness propio** (`make test-web`, dentro de `make test`):
  - ESLint `strictTypeChecked`, Prettier y `tsc` estricto;
  - `npm audit`;
  - Vitest con cobertura ≥ 85 % en líneas, ramas, funciones y sentencias.
- **Convivencia:** la consola Streamlit sigue en `:8501` y la web corre en `:8080`. Streamlit se retira en otro PR, cuando la guía de prueba manual pase completa en la consola web.

## Alternativas consideradas
- **nginx como proxy y la clave en memoria de JavaScript:** es más simple, pero un XSS podría leer la clave. Con el BFF, la clave nunca llega al navegador, igual que en Streamlit.
- **Mantener Streamlit como BFF y React solo para el mapa** (componente propio): obliga a mantener dos toolchains en el mismo servicio y no resuelve la re-ejecución de la página.
- **Next.js:** su servidor podría hacer de BFF, pero suma SSR y un runtime más pesado que la consola no necesita. Vite + Hono es más pequeño y más fácil de auditar.
- **CSS Modules o SCSS en vez de Tailwind + shadcn:** obligaría a construir y probar a mano diálogos, selects, pestañas y toasts accesibles.
- **vis-network (la librería que usa pyvis) en React:** sus opciones de estilo son menos expresivas que las hojas de estilo de Cytoscape, que se pueden probar como funciones puras (`lib/graph-elements.ts`).

## Consecuencias
- Hay una segunda toolchain (npm) y un cuarto harness. `make test` sigue siendo la única Definition of Done, y la CI agrega `web` a su matriz.
- Las sesiones viven en la memoria del BFF: al reiniciar el contenedor `web`, todos vuelven a iniciar sesión. Para la demo local es aceptable. Con varias réplicas haría falta un almacén compartido.
- La CSP admite `style-src 'unsafe-inline'`, porque Radix, sonner y Cytoscape fijan estilos en línea. No admite scripts en línea ni `eval`.
- Cytoscape fuerza `position: relative` en su contenedor, así que el mapa necesita una altura explícita (`size-full` dentro de un padre con altura). Una prueba lo vigila.
- El modelo del mapa (elementos, estilos y superposiciones) son funciones puras con pruebas unitarias. En jsdom, Cytoscape corre en modo *headless*.
- `.gitignore`: los patrones de `services/web` se anclan a la raíz del servicio (`/coverage/`, `/dist/`). Sin el ancla, `coverage/` ignoraba también `src/components/coverage/`, tanto para git como para el escáner de Tailwind. El `.gitignore` raíz excluye `lib/` (plantilla de Python), así que se re-incluyen `services/web/src/lib/` y `services/web/tests/lib/`.
- Al retirar Streamlit se eliminan `services/console`, su entrada en compose, en el Makefile y en la CI, y ADR 0005 y 0006 pasan a "Reemplazado por 0007".
