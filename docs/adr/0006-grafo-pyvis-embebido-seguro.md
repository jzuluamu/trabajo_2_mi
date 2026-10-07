# 0006 · Grafo interactivo con pyvis embebido de forma segura

- **Estado:** Aceptado
- **Fecha:** 2026-10-07

## Contexto
La consola mostraba la red solo como tablas, lo que obliga a interpretar ids y filas para entender qué base llega a qué zona. [ADR 0005](0005-consola-streamlit.md) ya preveía pyvis. Hacía falta un mapa con arrastre, zoom, hover y física, sin abrir una vía de ejecución de código desde los datos de la API: los nombres de bases, zonas y técnicos son texto libre que escribe un coordinador.

Hallazgos al revisar pyvis 0.3.2:
- Serializa nodos y aristas con `tojson` de Jinja, así que un nombre no puede cerrar el `<script>`.
- Su plantilla **siempre** carga Bootstrap desde `cdn.jsdelivr.net`, aunque se pida `cdn_resources="in_line"`.
- `st.iframe` (antes `st.components.v1.html`) con un string HTML ejecuta el contenido **en el mismo origen** que la app.

## Decisión
- **pyvis** construye los nodos y aristas, y su copia de **vis-network 9.1.2** se inserta en línea. El HTML lo genera una **plantilla propia** (`console/templates/graph.html`), sin la de pyvis.
- **Aislamiento:** el HTML se pasa a `st.iframe` como URL `data:text/html;base64,…`. El documento tiene así un **origen opaco** y no puede leer ni modificar la página de Streamlit.
- **CSP** en el propio documento:
  - `default-src 'none'`: sin red, fuentes ni recursos externos;
  - `script-src` solo con los **hash SHA-256** de los dos scripts propios (vis-network y `graph.js`): ningún otro script en línea se ejecuta, y no hay `eval`.
- **Datos:** viajan en un `<script type="application/json">` con `tojson`, que escapa `<`, `>`, `&` y `'`. vis-network muestra etiquetas y tooltips como texto plano. Donde un nombre entra en Markdown de Streamlit, se escapa con `md_escape`.
- **Física:** solo para estabilizar la disposición al cargar (`randomSeed` fijo, así el mapa sale igual cada vez). Luego se apaga para que los nodos no tiemblen y queden donde el usuario los arrastra.
- **Codificación visual** (ver [F4](../features/F4-consola.md#sistema-visual)):
  - bases cuadradas y zonas circulares;
  - zona sin conexión con borde punteado;
  - minutos en cada arista, cuya longitud crece con el costo;
  - flecha solo en los trayectos de un sentido;
  - selección con anillo ámbar y el resto atenuado.

## Alternativas consideradas
- **Plantilla de pyvis tal cual:** descartada por el CDN obligatorio y porque el HTML iría al mismo origen.
- **`st.components.v1.html` o `st.iframe` con un string HTML:** comparten el origen con la app. Además, Streamlit marca `components.v1.html` como obsoleto.
- **`streamlit-agraph` o un componente React propio:** agrega otra toolchain (npm), contra ADR 0005.
- **Imagen estática (matplotlib o graphviz):** no permite arrastrar ni hacer hover; no cumple la petición.

## Consecuencias
- No se puede devolver a Python el nodo seleccionado en el mapa (el iframe es de un solo sentido). La ficha se elige con un `selectbox`, y el mapa resalta esa selección.
- Cada vez que se redibuja la página se envían unos 650 KB (vis-network en línea, en base64). Es aceptable para el MVP. Si molesta, se puede servir vis-network como archivo estático del mismo servidor.
- pyvis arrastra dependencias pesadas (IPython y networkx) que **no** se usan para BFS ni Dijkstra ([AGENTS.md](../../AGENTS.md) §4); `pip-audit` las revisa.
- Para cambiar la plantilla o `graph.js` hay que mantener las pruebas de `tests/test_graph_view.py`: CSP con hash, ningún recurso externo y nombres maliciosos sin efecto.
