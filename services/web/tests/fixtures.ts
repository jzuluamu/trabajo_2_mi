import type { AttentionReport, CoverageReport, Network, RouteReport } from "@/lib/types";

/** Copia de seed/red_demo.json (la imagen de pruebas no incluye `seed/`). */
export const DEMO: Network = {
  nodes: [
    {
      id: "B_NORTE",
      type: "BASE",
      name: "Base Norte",
      technicians: [
        { id: "T01", name: "Ana", available: true },
        { id: "T02", name: "Luis", available: false },
      ],
    },
    {
      id: "B_SUR",
      type: "BASE",
      name: "Base Sur",
      technicians: [{ id: "T03", name: "Marta", available: true }],
    },
    {
      id: "B_OESTE",
      type: "BASE",
      name: "Base Oeste",
      technicians: [{ id: "T04", name: "Pedro", available: false }],
    },
    { id: "Z_ALAMEDA", type: "ZONE", name: "Alameda", technicians: [] },
    { id: "Z_BOSQUE", type: "ZONE", name: "Bosque", technicians: [] },
    { id: "Z_CENTRO", type: "ZONE", name: "Centro", technicians: [] },
    { id: "Z_COLINA", type: "ZONE", name: "Colina", technicians: [] },
    { id: "Z_DELICIAS", type: "ZONE", name: "Delicias", technicians: [] },
    { id: "Z_ESTACION", type: "ZONE", name: "Estación", technicians: [] },
    { id: "Z_FUENTE", type: "ZONE", name: "Fuente", technicians: [] },
    { id: "Z_ISLA", type: "ZONE", name: "Isla", technicians: [] },
  ],
  edges: [
    { id: "E01", source: "B_NORTE", target: "Z_CENTRO", weight: 30, bidirectional: true },
    { id: "E02", source: "B_NORTE", target: "Z_ALAMEDA", weight: 5, bidirectional: true },
    { id: "E03", source: "Z_ALAMEDA", target: "Z_BOSQUE", weight: 5, bidirectional: true },
    { id: "E04", source: "Z_BOSQUE", target: "Z_CENTRO", weight: 5, bidirectional: true },
    { id: "E05", source: "Z_CENTRO", target: "Z_COLINA", weight: 10, bidirectional: true },
    { id: "E06", source: "B_SUR", target: "Z_DELICIAS", weight: 8, bidirectional: true },
    { id: "E07", source: "Z_DELICIAS", target: "Z_COLINA", weight: 12, bidirectional: true },
    { id: "E08", source: "Z_DELICIAS", target: "Z_ESTACION", weight: 7, bidirectional: false },
    { id: "E09", source: "B_OESTE", target: "Z_FUENTE", weight: 6, bidirectional: true },
  ],
};

export const COVERAGE_NORTE: CoverageReport = {
  base: "B_NORTE",
  reachable: [
    { node_id: "Z_ALAMEDA", type: "ZONE", hops: 1 },
    { node_id: "Z_CENTRO", type: "ZONE", hops: 1 },
    { node_id: "Z_BOSQUE", type: "ZONE", hops: 2 },
    { node_id: "Z_COLINA", type: "ZONE", hops: 2 },
    { node_id: "Z_DELICIAS", type: "ZONE", hops: 3 },
    { node_id: "B_SUR", type: "BASE", hops: 4 },
    { node_id: "Z_ESTACION", type: "ZONE", hops: 4 },
  ],
  unreachable_zones: ["Z_FUENTE", "Z_ISLA"],
  zone: null,
  trace: null,
};

/** Respuesta real de routing-service para B_NORTE → Z_CENTRO en la red demo (docs/05). */
export const ROUTE_NORTE_CENTRO: RouteReport = {
  found: true,
  origin: "B_NORTE",
  destination: "Z_CENTRO",
  path: ["B_NORTE", "Z_ALAMEDA", "Z_BOSQUE", "Z_CENTRO"],
  total_cost: 15,
  hops: 3,
  legs: [
    { edge_id: "E02", from: "B_NORTE", to: "Z_ALAMEDA", weight: 5 },
    { edge_id: "E03", from: "Z_ALAMEDA", to: "Z_BOSQUE", weight: 5 },
    { edge_id: "E04", from: "Z_BOSQUE", to: "Z_CENTRO", weight: 5 },
  ],
  fewest_hops: { path: ["B_NORTE", "Z_CENTRO"], hops: 1, cost: 30 },
  message: "Ruta de menor costo: 15 min en 3 tramos (el camino de menos tramos cuesta 30 min).",
  trace: null,
};

export const ATTENTION_COLINA: AttentionReport = {
  zone: "Z_COLINA",
  found: true,
  best: {
    base: "B_SUR",
    technicians: [{ id: "T03", name: "Marta" }],
    path: ["B_SUR", "Z_DELICIAS", "Z_COLINA"],
    total_cost: 20,
    hops: 2,
  },
  alternatives: [{ base: "B_NORTE", total_cost: 25, hops: 4 }],
  message: "Atender desde B_SUR (Marta): 20 min.",
  trace: null,
};
