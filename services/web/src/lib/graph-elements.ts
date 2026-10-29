/**
 * Modelo puro del mapa de la red para Cytoscape: elementos, estilos y superposiciones.
 * El componente NetworkGraph solo aplica lo que calculan estas funciones.
 *
 * Codificación (docs/features/F4-consola.md §Sistema visual): cuadrado = base, círculo = zona,
 * borde punteado = sin conexión, flecha = solo ida, longitud de la arista = minutos. Los estados se
 * distinguen también por texto en la etiqueta (p. ej. "2 tramos", "sin cobertura"), no solo por color.
 */
import type { ElementDefinition, StylesheetJson } from "cytoscape";

import type { CoverageOverlay } from "@/lib/coverage-format";
import { formatMinutes, freeTechnicians, plural } from "@/lib/network-format";
import type { Network, NetworkEdge, NetworkNode } from "@/lib/types";

export const DRAFT_ID = "__draft__";
export const OVERLAY_CLASSES = [
  "selected",
  "neighbor",
  "faded",
  "origin",
  "reached",
  "hop-1",
  "hop-2",
  "hop-3",
  "hop-4",
  "unreached",
] as const;
type OverlayClass = (typeof OVERLAY_CLASSES)[number];

const FONT = "IBM Plex Sans, system-ui, sans-serif";
const MONO = "IBM Plex Mono, ui-monospace, monospace";

export interface GraphPalette {
  canvas: string;
  surface: string;
  ink: string;
  muted: string;
  base: string;
  baseIdle: string;
  zoneFill: string;
  zoneBorder: string;
  edge: string;
  edgeLabel: string;
  /** Selección y cobertura: el único color "de datos" del mapa. */
  accent: string;
  amber: string;
  amberSoft: string;
  error: string;
  greyFill: string;
  grey: string;
  hops: readonly [string, string, string, string];
}

/** Mapa neutro: grises en reposo; el azul aparece solo al seleccionar o consultar. */
export const LIGHT_PALETTE: GraphPalette = {
  canvas: "#FFFFFF",
  surface: "#FFFFFF",
  ink: "#171717",
  muted: "#737373",
  base: "#262626",
  baseIdle: "#A3A3A3",
  zoneFill: "#FFFFFF",
  zoneBorder: "#8A8A8A",
  edge: "#D4D4D4",
  edgeLabel: "#525252",
  accent: "#2563EB",
  amber: "#D97706",
  amberSoft: "#FFFBEB",
  error: "#DC2626",
  greyFill: "#F5F5F5",
  grey: "#B5B5B5",
  hops: ["#1D4ED8", "#3B82F6", "#93C5FD", "#DBEAFE"],
};

export const DARK_PALETTE: GraphPalette = {
  canvas: "#141414",
  surface: "#141414",
  ink: "#EDEDED",
  muted: "#A3A3A3",
  base: "#E5E5E5",
  baseIdle: "#5C5C5C",
  zoneFill: "#141414",
  zoneBorder: "#8A8A8A",
  edge: "#3D3D3D",
  edgeLabel: "#C4C4C4",
  accent: "#60A5FA",
  amber: "#FBBF24",
  amberSoft: "#2A2208",
  error: "#F87171",
  greyFill: "#1F1F1F",
  grey: "#5C5C5C",
  hops: ["#93C5FD", "#60A5FA", "#3B82F6", "#1E40AF"],
};

function degrees(network: Network): Map<string, number> {
  const degree = new Map(network.nodes.map((n) => [n.id, 0]));
  for (const edge of network.edges) {
    for (const end of [edge.source, edge.target]) degree.set(end, (degree.get(end) ?? 0) + 1);
  }
  return degree;
}

function baseLabel(node: NetworkNode, degree: number): string {
  if (node.type === "BASE") {
    const free = freeTechnicians(node);
    return `${node.name}\n${free ? plural(free, "técnico libre", "técnicos libres") : "sin técnicos libres"}`;
  }
  return degree === 0 ? `${node.name}\nsin conexión` : node.name;
}

function nodeTooltip(node: NetworkNode, degree: number): string {
  if (node.type === "BASE") {
    const free = freeTechnicians(node);
    return `${node.name} (${node.id}) · base · ${plural(node.technicians.length, "técnico", "técnicos")}, ${free} disponibles`;
  }
  const links =
    degree === 0 ? "sin trayectos: ninguna base llega" : plural(degree, "trayecto", "trayectos");
  return `${node.name} (${node.id}) · zona · ${links}`;
}

function edgeTooltip(edge: NetworkEdge, names: Map<string, string>): string {
  const arrow = edge.bidirectional ? "↔" : "→";
  const sense = edge.bidirectional ? "ambos sentidos" : "solo ida";
  return `${names.get(edge.source) ?? edge.source} ${arrow} ${names.get(edge.target) ?? edge.target} · ${formatMinutes(edge.weight)} · ${sense} (${edge.id})`;
}

/** Más minutos → arista más larga: el costo se percibe sin leer el número. */
export const idealEdgeLength = (weight: number): number => 50 + Math.min(weight, 60) * 2.5;

export function buildElements(network: Network): ElementDefinition[] {
  const degree = degrees(network);
  const names = new Map(network.nodes.map((n) => [n.id, n.name]));
  const sorted = [...network.nodes].sort((a, b) => a.id.localeCompare(b.id));
  const radius = 60 * Math.max(sorted.length, 3);
  const nodes: ElementDefinition[] = sorted.map((node, index) => {
    const d = degree.get(node.id) ?? 0;
    const angle = (2 * Math.PI * index) / sorted.length;
    const classes =
      node.type === "BASE"
        ? ["base", freeTechnicians(node) ? "free" : "idle"]
        : ["zone", ...(d === 0 ? ["isolated"] : [])];
    const label = baseLabel(node, d);
    return {
      group: "nodes",
      data: { id: node.id, label, baseLabel: label, tooltip: nodeTooltip(node, d) },
      classes,
      // Posición inicial determinista: el mapa sale igual cada vez (como randomSeed en ADR 0006).
      position: { x: radius * Math.cos(angle), y: radius * Math.sin(angle) },
    };
  });
  const edges: ElementDefinition[] = network.edges.map((edge) => ({
    group: "edges",
    data: {
      id: edge.id,
      source: edge.source,
      target: edge.target,
      weight: edge.weight,
      label: formatMinutes(edge.weight),
      tooltip: edgeTooltip(edge, names),
    },
    classes: edge.bidirectional ? [] : ["oneway"],
  }));
  return [...nodes, ...edges];
}

export interface DraftEdge {
  source: string;
  target: string;
  weight: number;
  bidirectional: boolean;
  valid: boolean;
}

export function draftElement(network: Network, draft: DraftEdge | null): ElementDefinition | null {
  const ids = new Set(network.nodes.map((n) => n.id));
  if (!draft || draft.source === draft.target || !ids.has(draft.source) || !ids.has(draft.target)) {
    return null;
  }
  return {
    group: "edges",
    data: {
      id: DRAFT_ID,
      source: draft.source,
      target: draft.target,
      weight: Math.max(draft.weight, 1),
      label: draft.valid ? `${formatMinutes(draft.weight)} · vista previa` : "revisar",
      tooltip: "Vista previa sin guardar",
    },
    classes: [
      "draft",
      ...(draft.valid ? [] : ["invalid"]),
      ...(draft.bidirectional ? [] : ["oneway"]),
    ],
  };
}

export interface Overlay {
  classes: Map<string, OverlayClass[]>;
  labels: Map<string, string>;
}

function add(map: Map<string, OverlayClass[]>, id: string, ...classes: OverlayClass[]): void {
  map.set(id, [...(map.get(id) ?? []), ...classes]);
}

export function overlayFor(
  network: Network,
  {
    selected = null,
    coverage = null,
  }: { selected?: string | null; coverage?: CoverageOverlay | null },
): Overlay {
  const classes = new Map<string, OverlayClass[]>();
  const labels = new Map<string, string>();
  const ids = new Set(network.nodes.map((n) => n.id));

  if (coverage && ids.has(coverage.origin)) {
    const covered = new Set([coverage.origin, ...coverage.hops.keys()]);
    for (const node of network.nodes) {
      const hops = coverage.hops.get(node.id);
      if (node.id === coverage.origin) {
        add(classes, node.id, "origin");
        labels.set(node.id, `${node.name}\norigen`);
      } else if (hops !== undefined) {
        add(classes, node.id, "reached", `hop-${Math.min(hops, 4)}` as OverlayClass);
        labels.set(node.id, `${node.name}\n${plural(hops, "tramo", "tramos")}`);
      } else if (coverage.unreachable.has(node.id)) {
        add(classes, node.id, "unreached");
        labels.set(node.id, `${node.name}\nsin cobertura`);
      } else {
        add(classes, node.id, "faded");
      }
    }
    for (const edge of network.edges) {
      add(
        classes,
        edge.id,
        covered.has(edge.source) && covered.has(edge.target) ? "reached" : "faded",
      );
    }
    if (selected && ids.has(selected)) add(classes, selected, "selected");
    return { classes, labels };
  }

  if (selected && ids.has(selected)) {
    const neighbors = new Set([selected]);
    for (const edge of network.edges) {
      if (edge.source === selected || edge.target === selected) {
        neighbors.add(edge.source).add(edge.target);
        add(classes, edge.id, "neighbor");
      } else {
        add(classes, edge.id, "faded");
      }
    }
    for (const node of network.nodes) {
      if (node.id === selected) add(classes, node.id, "selected");
      else if (!neighbors.has(node.id)) add(classes, node.id, "faded");
    }
  }
  return { classes, labels };
}

export function graphSummary(network: Network): string {
  const bases = network.nodes.filter((n) => n.type === "BASE").length;
  const zones = network.nodes.length - bases;
  return `Mapa de la red: ${plural(bases, "base", "bases")}, ${plural(zones, "zona", "zonas")} y ${plural(network.edges.length, "trayecto", "trayectos")}. El detalle está en la ficha y en la tabla.`;
}

export function graphStyle(p: GraphPalette): StylesheetJson {
  const strong = { "line-color": p.accent, "target-arrow-color": p.accent, width: 3 };
  return [
    {
      selector: "node",
      style: {
        label: "data(label)",
        "text-wrap": "wrap",
        "text-valign": "bottom",
        "text-halign": "center",
        "text-margin-y": 6,
        "font-family": FONT,
        "font-size": 15,
        color: p.ink,
        "text-background-color": p.canvas,
        "text-background-opacity": 0.9,
        "text-background-padding": "2px",
        "text-background-shape": "roundrectangle",
        width: 28,
        height: 28,
        "border-width": 2,
        "overlay-opacity": 0,
        "transition-property": "opacity, background-color, border-color, border-width",
        "transition-duration": 200,
      },
    },
    {
      selector: "node.base",
      style: {
        shape: "round-rectangle",
        width: 34,
        height: 34,
        "background-color": p.base,
        "border-color": p.surface,
        "border-width": 3,
      },
    },
    { selector: "node.base.idle", style: { "background-color": p.baseIdle } },
    {
      selector: "node.zone",
      style: { shape: "ellipse", "background-color": p.zoneFill, "border-color": p.zoneBorder },
    },
    {
      selector: "node.zone.isolated",
      style: {
        "background-color": p.greyFill,
        "border-color": p.grey,
        "border-style": "dashed",
        color: p.muted,
      },
    },
    {
      selector: "edge",
      style: {
        width: 2,
        "curve-style": "bezier",
        "line-color": p.edge,
        "target-arrow-color": p.edge,
        "target-arrow-shape": "none",
        "arrow-scale": 1.1,
        label: "data(label)",
        "font-family": MONO,
        "font-size": 12,
        color: p.edgeLabel,
        "text-background-color": p.surface,
        "text-background-opacity": 1,
        "text-background-padding": "2px",
        "text-background-shape": "roundrectangle",
        "overlay-opacity": 0,
        "transition-property": "opacity, line-color, width",
        "transition-duration": 200,
      },
    },
    { selector: "edge.oneway", style: { "target-arrow-shape": "triangle" } },
    { selector: ".faded", style: { opacity: 0.35 } },
    { selector: "node.selected", style: { "border-color": p.accent, "border-width": 4 } },
    { selector: "edge.neighbor", style: strong },
    {
      selector: "node.origin",
      style: { "background-color": p.accent, "border-color": p.amber, "border-width": 4 },
    },
    { selector: "node.reached.hop-1", style: { "background-color": p.hops[0] } },
    { selector: "node.reached.hop-2", style: { "background-color": p.hops[1] } },
    { selector: "node.reached.hop-3", style: { "background-color": p.hops[2] } },
    { selector: "node.reached.hop-4", style: { "background-color": p.hops[3] } },
    { selector: "node.reached", style: { "border-color": p.accent } },
    {
      selector: "node.unreached",
      style: {
        "background-color": p.greyFill,
        "border-color": p.grey,
        "border-style": "dashed",
        color: p.muted,
      },
    },
    { selector: "edge.reached", style: strong },
    {
      selector: "edge.draft",
      style: {
        width: 3,
        "line-style": "dashed",
        "line-dash-pattern": [8, 6],
        "line-color": p.amber,
        "target-arrow-color": p.amber,
        color: p.amber,
        "text-background-color": p.amberSoft,
      },
    },
    {
      selector: "edge.draft.invalid",
      style: { "line-color": p.error, "target-arrow-color": p.error, color: p.error },
    },
  ];
}
