"""Grafo pyvis: codificación visual y seguridad del HTML embebido (ADR 0006)."""

import re
from typing import Any

import pytest

from console.graph_view import (
    AMBER_STRONG,
    BLUE,
    BLUE_IDLE,
    DRAFT_ID,
    ERROR,
    DraftEdge,
    csp_hash,
    graph_html,
    graph_payload,
)

ATTACK = "</script><script>alert(1)</script><img src=x onerror=alert(2)>"


def _node(node_id: str, kind: str = "ZONE", name: str = "", **extra: Any) -> dict[str, Any]:
    return {"id": node_id, "type": kind, "name": name or node_id, "technicians": [], **extra}


def _edge(edge_id: str, source: str, target: str, weight: float = 5, bi: bool = True) -> Any:
    return {"id": edge_id, "source": source, "target": target, "weight": weight,
            "bidirectional": bi}  # fmt: skip


NETWORK: dict[str, Any] = {
    "nodes": [
        _node("B_NORTE", "BASE", "Base Norte",
              technicians=[{"id": "T01", "name": "Ana", "available": True}]),
        _node("B_OESTE", "BASE", "Base Oeste",
              technicians=[{"id": "T04", "name": "Pedro", "available": False}]),
        _node("Z_CENTRO", name="Centro"),
        _node("Z_ESTACION", name="Estación"),
        _node("Z_ISLA", name="Isla"),
    ],
    "edges": [
        _edge("E01", "B_NORTE", "Z_CENTRO", 30),
        _edge("E02", "B_NORTE", "Z_ESTACION", 5),
        _edge("E08", "Z_CENTRO", "Z_ESTACION", 7, bi=False),
        _edge("E09", "Z_ESTACION", "Z_CENTRO", 9, bi=False),
        _edge("E10", "B_OESTE", "Z_CENTRO", 6),
    ],
}  # fmt: skip


def _by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["id"]): item for item in items}


# --- seguridad ----------------------------------------------------------------------------


def test_malicious_names_cannot_break_out_of_the_data_block() -> None:
    network = {"nodes": [_node("Z_X", name=ATTACK)], "edges": []}

    html = graph_html(network)

    assert ATTACK not in html
    assert "</script><script>alert(1)" not in html
    assert graph_payload(html)["nodes"][0]["label"].startswith(ATTACK)  # se muestra como texto


def test_csp_allows_only_the_two_hashed_scripts_and_no_network() -> None:
    html = graph_html(NETWORK)

    csp = re.search(r'Content-Security-Policy" content="([^"]+)"', html)
    assert csp is not None
    policy = csp.group(1)
    assert "default-src 'none'" in policy
    assert "unsafe-inline" not in policy.split("script-src")[1].split(";")[0]
    assert "unsafe-eval" not in policy
    scripts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    assert len(scripts) == 2
    assert all(csp_hash(script) in policy for script in scripts)


def test_no_external_resources_are_loaded() -> None:
    markup = re.sub(r"<script>.*?</script>", "", graph_html(NETWORK), flags=re.DOTALL)

    assert re.findall(r"(?:src|href)\s*=", markup) == []
    assert "<link" not in markup


def test_empty_network_renders_message_without_scripts() -> None:
    html = graph_html({"nodes": [], "edges": []})

    assert "La red está vacía" in html
    assert "<script>" not in html


# --- codificación visual --------------------------------------------------------------------


def test_bases_and_zones_have_distinct_shapes_and_states() -> None:
    nodes = _by_id(graph_payload(graph_html(NETWORK))["nodes"])

    assert nodes["B_NORTE"]["shape"] == "square"
    assert nodes["B_NORTE"]["color"]["background"] == BLUE
    assert nodes["B_NORTE"]["label"] == "Base Norte\n1 técnico libre"
    assert nodes["B_OESTE"]["color"]["background"] == BLUE_IDLE
    assert nodes["B_OESTE"]["label"] == "Base Oeste\nsin técnicos libres"
    assert nodes["Z_CENTRO"]["shape"] == "dot"
    assert "shapeProperties" not in nodes["Z_CENTRO"]
    assert nodes["Z_ISLA"]["shapeProperties"] == {"borderDashes": [4, 4]}
    assert nodes["Z_ISLA"]["label"] == "Isla\nsin conexión"


def test_edges_show_minutes_direction_and_cost_as_length() -> None:
    edges = _by_id(graph_payload(graph_html(NETWORK))["edges"])

    assert edges["E01"]["label"] == "30 min"
    assert edges["E01"]["arrows"]["to"]["enabled"] is False
    assert edges["E08"]["arrows"]["to"]["enabled"] is True
    assert edges["E01"]["length"] > edges["E02"]["length"]
    assert edges["E08"]["smooth"]["type"] == "curvedCW"  # E08 y E09 son pares opuestos
    assert "smooth" not in edges["E01"]
    assert edges["E08"]["title"] == "Centro → Estación · 7 min · solo ida (E08)"


@pytest.mark.parametrize(
    ("valid", "color", "label"),
    [(True, AMBER_STRONG, "12 min · vista previa"), (False, ERROR, "revisar")],
)
def test_draft_edge_is_dashed_and_colored_by_validity(valid: bool, color: str, label: str) -> None:
    draft = DraftEdge("Z_ISLA", "B_NORTE", 12, bidirectional=False, valid=valid)

    edges = _by_id(graph_payload(graph_html(NETWORK, draft=draft))["edges"])

    assert edges[DRAFT_ID]["dashes"] == [8, 6]
    assert edges[DRAFT_ID]["color"]["color"] == color
    assert edges[DRAFT_ID]["label"] == label
    assert edges[DRAFT_ID]["physics"] is False
    assert edges[DRAFT_ID]["arrows"]["to"]["enabled"] is True


def test_draft_with_unknown_node_is_ignored() -> None:
    draft = DraftEdge("Z_NO", "B_NORTE", 12, bidirectional=True, valid=True)

    edges = graph_payload(graph_html(NETWORK, draft=draft))["edges"]

    assert DRAFT_ID not in {edge["id"] for edge in edges}


@pytest.mark.parametrize(("selected", "expected"), [("Z_CENTRO", "Z_CENTRO"), ("NOPE", None)])
def test_selected_node_is_passed_only_if_it_exists(selected: str, expected: str | None) -> None:
    assert graph_payload(graph_html(NETWORK, selected=selected))["selected"] == expected
