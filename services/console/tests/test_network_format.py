from typing import Any

import pytest

from console.clients.http import ApiClientError
from console.network_format import (
    FormInputError,
    edge_payload,
    edge_rows,
    error_text,
    md_escape,
    network_kpis,
    node_card,
    node_payload,
    node_rows,
    parse_network_file,
    parse_technicians,
)


def test_zone_without_technicians_shows_dash() -> None:
    network = {"nodes": [{"id": "Z_ISLA", "type": "ZONE", "name": "Isla", "technicians": []}]}

    assert node_rows(network) == [
        {"ID": "Z_ISLA", "Tipo": "Zona", "Nombre": "Isla", "Técnicos": "—"}
    ]


def test_one_way_edge_is_labelled() -> None:
    edge = {"id": "E08", "source": "A", "target": "B", "weight": 7.0, "bidirectional": False}

    assert edge_rows({"edges": [edge]})[0]["Sentido"] == "→ solo ida"


def test_parse_technicians_defaults_available_and_skips_blank_lines() -> None:
    text = "T10; Sara\n\n T11 ; Juan ; NO \nT12; Eva; disponible"

    assert parse_technicians(text) == [
        {"id": "T10", "name": "Sara", "available": True},
        {"id": "T11", "name": "Juan", "available": False},
        {"id": "T12", "name": "Eva", "available": True},
    ]


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("T10", "Técnico en la línea 1: use el formato 'ID; Nombre; sí/no'."),
        ("T10; Sara; quizás", "Técnico en la línea 1: la disponibilidad debe ser 'sí' o 'no'."),
    ],
)
def test_parse_technicians_rejects_bad_lines(text: str, message: str) -> None:
    with pytest.raises(FormInputError, match=message):
        parse_technicians(text)


def test_node_payload_for_zone_has_no_technicians() -> None:
    assert node_payload(" Z_X ", "ZONE", " Equis ", "") == {
        "id": "Z_X",
        "type": "ZONE",
        "name": "Equis",
    }


def test_edge_payload() -> None:
    assert edge_payload(" E1 ", "A", "B", 5.0, False) == {
        "id": "E1",
        "source": "A",
        "target": "B",
        "weight": 5.0,
        "bidirectional": False,
    }


def test_parse_network_file_keeps_lists_and_sets_replace() -> None:
    content = b'{"replace": true, "nodes": [{"id": "A"}], "edges": []}'

    assert parse_network_file(content, replace=False) == {
        "nodes": [{"id": "A"}],
        "edges": [],
        "replace": False,
    }


def test_parse_network_file_rejects_non_utf8() -> None:
    with pytest.raises(FormInputError):
        parse_network_file(b"\xff\xfe", replace=True)


def test_error_text_lists_validation_fields() -> None:
    error = ApiClientError(
        "VALIDATION_ERROR",
        "La solicitud contiene datos inválidos.",
        422,
        {"errors": [{"field": "body.weight", "message": "x"}, "ignorado"]},
    )

    assert error_text(error) == "La solicitud contiene datos inválidos. Campos: weight."


def test_error_text_points_to_import_node() -> None:
    error = ApiClientError("DUPLICATE_ID", "Ya existe.", 409, {"section": "nodes", "index": 0})

    assert error_text(error) == "Ya existe. (archivo: nodo #1)"


DEMO_LIKE: dict[str, Any] = {
    "nodes": [
        {"id": "B_NORTE", "type": "BASE", "name": "Base Norte",
         "technicians": [{"id": "T01", "name": "Ana", "available": True}]},
        {"id": "B_OESTE", "type": "BASE", "name": "Base Oeste",
         "technicians": [{"id": "T04", "name": "Pedro", "available": False}]},
        {"id": "B_SOLA", "type": "BASE", "name": "Base Sola", "technicians": []},
        {"id": "Z_CENTRO", "type": "ZONE", "name": "Centro", "technicians": []},
        {"id": "Z_ISLA", "type": "ZONE", "name": "Isla", "technicians": []},
    ],
    "edges": [
        {"id": "E01", "source": "B_NORTE", "target": "Z_CENTRO", "weight": 30.0,
         "bidirectional": True},
        {"id": "E02", "source": "Z_CENTRO", "target": "B_OESTE", "weight": 7.0,
         "bidirectional": False},
    ],
}  # fmt: skip


def test_network_kpis() -> None:
    assert network_kpis(DEMO_LIKE) == [
        ("3", "Bases", "1 con técnico libre"),
        ("2", "Zonas", "1 con trayectos"),
        ("2", "Trayectos", "1 de un solo sentido"),
        ("1", "Zonas sin conexión", "ninguna base llega"),
    ]


def test_network_kpis_when_all_zones_are_connected() -> None:
    network = {"nodes": [DEMO_LIKE["nodes"][3]], "edges": []}

    assert network_kpis(network)[3] == ("1", "Zonas sin conexión", "ninguna base llega")
    assert network_kpis({"nodes": [], "edges": []})[3][2] == "todas conectadas"


def test_node_card_for_zone_lists_directions() -> None:
    card = node_card(DEMO_LIKE, "Z_CENTRO")

    assert card is not None
    assert card["title"] == "Centro · Zona"
    assert card["links"] == [
        {"Trayecto": "↔ Base Norte", "Minutos": 30.0, "Conexión": "E01"},
        {"Trayecto": "→ Base Oeste", "Minutos": 7.0, "Conexión": "E02"},
    ]
    assert card["note"] == ""


@pytest.mark.parametrize(
    ("node_id", "note"),
    [
        ("B_OESTE", "Base sin técnicos disponibles: llega a sus zonas, pero no puede atenderlas."),
        ("B_SOLA", "Base sin trayectos: no puede llegar a ninguna zona."),
        ("Z_ISLA", "Sin trayectos registrados: ninguna base puede llegar a esta zona."),
    ],
)
def test_node_card_warns_about_unusable_nodes(node_id: str, note: str) -> None:
    card = node_card(DEMO_LIKE, node_id)

    assert card is not None
    assert card["note"] == note


def test_node_card_incoming_one_way_and_technicians() -> None:
    card = node_card(DEMO_LIKE, "B_OESTE")

    assert card is not None
    assert card["links"][0]["Trayecto"] == "← Centro"
    assert card["technicians"] == [{"label": "Pedro (T04)", "available": False}]


def test_node_card_unknown_node() -> None:
    assert node_card(DEMO_LIKE, "NOPE") is None


def test_md_escape_neutralizes_markdown() -> None:
    assert md_escape("[x](http://e.vil) **b** #h") == (
        "\\[x\\]\\(http\\://e\\.vil\\) \\*\\*b\\*\\* \\#h"
    )
