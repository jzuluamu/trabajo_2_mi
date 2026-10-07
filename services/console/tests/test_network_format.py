import pytest

from console.clients.http import ApiClientError
from console.network_format import (
    FormInputError,
    edge_payload,
    edge_rows,
    error_text,
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
