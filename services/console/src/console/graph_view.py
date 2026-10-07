"""Grafo interactivo de la red con pyvis (vis-network 9.1.2), embebido de forma segura.

pyvis construye los nodos y aristas; el HTML lo genera una plantilla PROPIA
(`templates/graph.html`), porque la de pyvis carga Bootstrap desde un CDN aunque se pida
`cdn_resources="in_line"`. Seguridad (ADR 0006):
- vis-network se inserta en línea desde el paquete pyvis: el iframe no pide nada a internet;
- CSP `default-src 'none'` y `script-src` solo con los hash SHA-256 de los dos scripts propios:
  sin red, sin `eval` y ningún otro script en línea se ejecuta;
- los datos van con `tojson` de Jinja, que escapa `<`, `>`, `&` y `'`: un nombre como
  `</script><script>…` no puede inyectar código; los tooltips de vis-network son texto plano.
"""

import base64
import hashlib
import json
from dataclasses import dataclass
from functools import lru_cache
from importlib.resources import files
from pathlib import Path
from typing import Any

import pyvis
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pyvis.network import Network

from console.network_format import JsonDict

# Paleta (docs/features/F4-consola.md §Sistema visual): azules análogos + ámbar complementario.
INK, MUTED = "#0F2540", "#4A5D78"
BLUE, BLUE_IDLE, BLUE_DARK = "#1F5FBF", "#8CA3C3", "#174A96"
ZONE_FILL, ZONE_BORDER = "#DCEBFB", "#5B8FD6"
EDGE_REST = "#8FA9CC"
AMBER, AMBER_STRONG = "#F2B661", "#E08A1E"
ERROR = "#B42318"
GREY_FILL, GREY = "#F1F4F8", "#9AA8BA"
CANVAS = "#F8FAFD"

DRAFT_ID = "__draft__"
FONT = "IBM Plex Sans, system-ui, -apple-system, Segoe UI, sans-serif"
MONO = "IBM Plex Mono, ui-monospace, SFMono-Regular, Menlo, monospace"

OPTIONS: JsonDict = {
    "autoResize": True,
    "layout": {"randomSeed": 7, "improvedLayout": True},
    "physics": {
        "enabled": True,
        "solver": "forceAtlas2Based",
        "forceAtlas2Based": {
            "gravitationalConstant": -70,
            "centralGravity": 0.012,
            "springConstant": 0.05,
            "avoidOverlap": 0.7,
        },
        "stabilization": {"enabled": True, "iterations": 500, "fit": True},
    },
    "interaction": {
        "hover": True,
        "tooltipDelay": 120,
        "dragNodes": True,
        "dragView": True,
        "zoomView": True,
        "multiselect": False,
        "navigationButtons": False,
        "keyboard": {"enabled": False},
    },
    "nodes": {"font": {"face": FONT, "size": 15, "color": INK, "multi": False}},
    "edges": {"smooth": False, "selectionWidth": 1.5, "hoverWidth": 1},
}


@dataclass(frozen=True)
class DraftEdge:
    """Conexión que el coordinador está escribiendo, dibujada antes de guardarla."""

    source: str
    target: str
    weight: float
    bidirectional: bool
    valid: bool


def _available(node: JsonDict) -> int:
    return sum(1 for t in node.get("technicians", []) if t.get("available"))


def _degree(network: JsonDict) -> dict[str, int]:
    degree = {node["id"]: 0 for node in network.get("nodes", [])}
    for edge in network.get("edges", []):
        for end in (edge["source"], edge["target"]):
            degree[end] = degree.get(end, 0) + 1
    return degree


def _node_attrs(node: JsonDict, degree: int) -> JsonDict:
    name, node_id = str(node["name"]), str(node["id"])
    if node["type"] == "BASE":
        total, free = len(node.get("technicians", [])), _available(node)
        fill = BLUE if free else BLUE_IDLE
        summary = f"{free} técnico{'s' if free != 1 else ''} libre{'s' if free != 1 else ''}"
        return {
            "label": f"{name}\n{summary if free else 'sin técnicos libres'}",
            "title": f"{name} ({node_id}) · base · {total} técnicos, {free} disponibles",
            "shape": "square",
            "size": 20,
            "borderWidth": 3,
            "borderWidthSelected": 5,
            "color": {
                "background": fill,
                "border": "#FFFFFF",
                "highlight": {"background": fill, "border": AMBER},
                "hover": {"background": BLUE_DARK if free else BLUE_IDLE, "border": "#FFFFFF"},
            },
            "font": {"color": INK, "size": 15, "face": FONT},
        }
    isolated = degree == 0
    fill, border = (GREY_FILL, GREY) if isolated else (ZONE_FILL, ZONE_BORDER)
    attrs: JsonDict = {
        "label": f"{name}\nsin conexión" if isolated else name,
        "title": f"{name} ({node_id}) · zona · "
        + ("sin trayectos: ninguna base llega" if isolated else f"{degree} trayectos"),
        "shape": "dot",
        "size": 14,
        "borderWidth": 2,
        "borderWidthSelected": 5,
        "color": {
            "background": fill,
            "border": border,
            "highlight": {"background": fill, "border": AMBER},
            "hover": {"background": "#C9DEF7" if not isolated else GREY_FILL, "border": border},
        },
        "font": {"color": MUTED if isolated else INK, "size": 14, "face": FONT},
    }
    if isolated:
        attrs["shapeProperties"] = {"borderDashes": [4, 4]}
    return attrs


def _edge_length(weight: float) -> int:
    """Más minutos → arista más larga: el costo se percibe sin leer el número."""
    return int(70 + min(weight, 60) * 6)


def _edge_attrs(edge: JsonDict, names: dict[str, str], *, twin: bool) -> JsonDict:
    weight = float(edge["weight"])
    sense = "ambos sentidos" if edge["bidirectional"] else "solo ida"
    arrow = "↔" if edge["bidirectional"] else "→"
    attrs: JsonDict = {
        "id": edge["id"],
        "label": f"{weight:g} min",
        "title": f"{names[edge['source']]} {arrow} {names[edge['target']]} · "
        f"{weight:g} min · {sense} ({edge['id']})",
        "width": 2,
        "length": _edge_length(weight),
        "color": {"color": EDGE_REST, "highlight": BLUE, "hover": BLUE},
        "arrows": {"to": {"enabled": not edge["bidirectional"], "scaleFactor": 0.8}},
        "font": {
            "face": MONO,
            "size": 13,
            "color": BLUE_DARK,
            "strokeWidth": 0,
            "background": "#FFFFFF",
            "align": "horizontal",
        },
    }
    if twin:  # A→B y B→A como conexiones distintas: se curvan para no superponerse
        attrs["smooth"] = {"enabled": True, "type": "curvedCW", "roundness": 0.18}
    return attrs


def _draft_attrs(draft: DraftEdge) -> JsonDict:
    color = AMBER_STRONG if draft.valid else ERROR
    return {
        "id": DRAFT_ID,
        "label": f"{draft.weight:g} min · vista previa" if draft.valid else "revisar",
        "title": "Vista previa sin guardar",
        "width": 3,
        "dashes": [8, 6],
        "length": _edge_length(max(draft.weight, 1)),
        "physics": False,
        "color": {"color": color, "highlight": color, "hover": color},
        "arrows": {"to": {"enabled": not draft.bidirectional, "scaleFactor": 0.8}},
        "font": {"face": MONO, "size": 13, "color": color, "strokeWidth": 0,
                 "background": "#FFF4E5", "align": "horizontal"},
    }  # fmt: skip


def build_network(network: JsonDict, draft: DraftEdge | None = None) -> Network:
    """Red de pyvis con los estilos del sistema visual (sin generar HTML)."""
    net = Network(directed=True, cdn_resources="in_line")
    degree = _degree(network)
    names = {str(node["id"]): str(node["name"]) for node in network.get("nodes", [])}
    for node in network.get("nodes", []):
        net.add_node(str(node["id"]), **_node_attrs(node, degree.get(node["id"], 0)))
    pairs = {(e["source"], e["target"]) for e in network.get("edges", [])}
    for edge in network.get("edges", []):
        twin = (edge["target"], edge["source"]) in pairs
        net.add_edge(edge["source"], edge["target"], **_edge_attrs(edge, names, twin=twin))
    if draft and draft.source in names and draft.target in names:
        net.add_edge(draft.source, draft.target, **_draft_attrs(draft))
    return net


@lru_cache
def _vis_js() -> str:
    script = (Path(pyvis.__file__).parent / "lib" / "vis-9.1.2" / "vis-network.min.js").read_text(
        "utf-8"
    )
    if "</script" in script.lower():  # nunca debería ocurrir; protege el cierre del <script>
        raise ValueError("vis-network.min.js contiene '</script'")
    return script


def _templates_dir() -> Path:
    return Path(str(files("console").joinpath("templates")))


@lru_cache
def _app_js() -> str:
    return (_templates_dir() / "graph.js").read_text("utf-8")


def csp_hash(script: str) -> str:
    """Fuente CSP `'sha256-…'` de un script en línea: solo se ejecuta ese texto exacto."""
    digest = hashlib.sha256(script.encode("utf-8")).digest()
    return f"'sha256-{base64.b64encode(digest).decode('ascii')}'"


@lru_cache
def _environment() -> Environment:
    templates = _templates_dir()
    return Environment(
        loader=FileSystemLoader(templates),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )


def graph_html(
    network: JsonDict,
    *,
    selected: str | None = None,
    draft: DraftEdge | None = None,
    height: int = 560,
) -> str:
    """HTML autocontenido del grafo, para `st.components.v1.html` (iframe aislado)."""
    net = build_network(network, draft)
    data: dict[str, Any] = {
        "nodes": net.nodes,
        "edges": net.edges,
        "options": OPTIONS,
        "selected": selected if selected in net.get_nodes() else None,
    }
    template = _environment().get_template("graph.html")
    return template.render(
        data=data,
        height=height,
        canvas=CANVAS,
        vis_js=_vis_js(),
        app_js=_app_js(),
        script_hashes=f"{csp_hash(_vis_js())} {csp_hash(_app_js())}",
        empty=not net.nodes,
    )


def graph_payload(html: str) -> JsonDict:
    """Extrae los datos serializados del HTML (para pruebas y depuración)."""
    marker = 'id="graph-data" type="application/json">'
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    payload: JsonDict = json.loads(html[start:end])
    return payload
