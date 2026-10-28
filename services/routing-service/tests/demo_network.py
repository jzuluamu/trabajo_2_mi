"""Red demo (`seed/red_demo.json`) como datos de prueba, sin leer archivos ni usar la red."""

from typing import Any

from routing_service.domain.graph import Graph, Node, NodeType, Technician

DEMO_PAYLOAD: dict[str, Any] = {
    "nodes": [
        {
            "id": "B_NORTE",
            "type": "BASE",
            "name": "Base Norte",
            "technicians": [
                {"id": "T01", "name": "Ana", "available": True},
                {"id": "T02", "name": "Luis", "available": False},
            ],
        },
        {
            "id": "B_OESTE",
            "type": "BASE",
            "name": "Base Oeste",
            "technicians": [{"id": "T04", "name": "Pedro", "available": False}],
        },
        {
            "id": "B_SUR",
            "type": "BASE",
            "name": "Base Sur",
            "technicians": [{"id": "T03", "name": "Marta", "available": True}],
        },
        {"id": "Z_ALAMEDA", "type": "ZONE", "name": "Alameda", "technicians": []},
        {"id": "Z_BOSQUE", "type": "ZONE", "name": "Bosque", "technicians": []},
        {"id": "Z_CENTRO", "type": "ZONE", "name": "Centro", "technicians": []},
        {"id": "Z_COLINA", "type": "ZONE", "name": "Colina", "technicians": []},
        {"id": "Z_DELICIAS", "type": "ZONE", "name": "Delicias", "technicians": []},
        {"id": "Z_ESTACION", "type": "ZONE", "name": "Estación", "technicians": []},
        {"id": "Z_FUENTE", "type": "ZONE", "name": "Fuente", "technicians": []},
        {"id": "Z_ISLA", "type": "ZONE", "name": "Isla", "technicians": []},
    ],
    "edges": [
        {
            "id": "E01",
            "source": "B_NORTE",
            "target": "Z_CENTRO",
            "weight": 30,
            "bidirectional": True,
        },
        {
            "id": "E02",
            "source": "B_NORTE",
            "target": "Z_ALAMEDA",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E03",
            "source": "Z_ALAMEDA",
            "target": "Z_BOSQUE",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E04",
            "source": "Z_BOSQUE",
            "target": "Z_CENTRO",
            "weight": 5,
            "bidirectional": True,
        },
        {
            "id": "E05",
            "source": "Z_CENTRO",
            "target": "Z_COLINA",
            "weight": 10,
            "bidirectional": True,
        },
        {
            "id": "E06",
            "source": "B_SUR",
            "target": "Z_DELICIAS",
            "weight": 8,
            "bidirectional": True,
        },
        {
            "id": "E07",
            "source": "Z_DELICIAS",
            "target": "Z_COLINA",
            "weight": 12,
            "bidirectional": True,
        },
        {
            "id": "E08",
            "source": "Z_DELICIAS",
            "target": "Z_ESTACION",
            "weight": 7,
            "bidirectional": False,
        },
        {
            "id": "E09",
            "source": "B_OESTE",
            "target": "Z_FUENTE",
            "weight": 6,
            "bidirectional": True,
        },
    ],
}


def demo_graph() -> Graph:
    graph = Graph()
    for item in DEMO_PAYLOAD["nodes"]:
        technicians = tuple(
            Technician(t["id"], t["name"], t["available"]) for t in item["technicians"]
        )
        graph.add_node(Node(item["id"], NodeType(item["type"]), item["name"], technicians))
    for edge in DEMO_PAYLOAD["edges"]:
        graph.add_edge(
            edge["id"],
            edge["source"],
            edge["target"],
            edge["weight"],
            bidirectional=edge["bidirectional"],
        )
    return graph
