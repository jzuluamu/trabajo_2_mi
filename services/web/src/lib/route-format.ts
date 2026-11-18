/**
 * Transformaciones puras de las respuestas de F3 (ruta de menor costo y mejor atención) a lo que
 * muestra la consola: superposición del mapa, itinerario y textos con nombres en vez de ids.
 */
import { formatMinutes, joinList, plural } from "@/lib/network-format";
import type { AttentionReport, Network, RouteReport } from "@/lib/types";

const names = (network: Network): Map<string, string> =>
  new Map(network.nodes.map((node) => [node.id, node.name]));

/** Conexión del mapa recorrida por la ruta; `forward` = en el sentido `source` → `target`. */
export interface RouteEdge {
  id: string;
  forward: boolean;
}

/** Lo que el mapa debe resaltar de una ruta (docs/features/F4-consola.md §Menor costo). */
export interface RouteOverlay {
  origin: string;
  destination: string;
  path: string[];
  edges: RouteEdge[];
  /** Minutos acumulados al llegar a cada parada de la ruta. */
  arrivals: ReadonlyMap<string, number>;
  /** Conexiones del camino de menos tramos que la ruta más rápida no usa. */
  alternative: string[];
}

/**
 * Conexiones que recorren `path` en orden. La mejor atención solo trae los nodos del camino, así
 * que se buscan en la red: el mismo par (`source`, `target`), o el inverso si es de ida y vuelta.
 */
export function pathEdges(network: Network, path: readonly string[]): RouteEdge[] {
  const edges: RouteEdge[] = [];
  for (let i = 0; i + 1 < path.length; i += 1) {
    const [from, to] = [path[i], path[i + 1]];
    const forward = network.edges.find((e) => e.source === from && e.target === to);
    const backward = network.edges.find(
      (e) => e.bidirectional && e.source === to && e.target === from,
    );
    if (forward) edges.push({ id: forward.id, forward: true });
    else if (backward) edges.push({ id: backward.id, forward: false });
  }
  return edges;
}

function arrivalsAlong(network: Network, path: readonly string[], edges: RouteEdge[]) {
  const weights = new Map(network.edges.map((edge) => [edge.id, edge.weight]));
  const arrivals = new Map<string, number>();
  let total = 0;
  path.forEach((node, index) => {
    if (index > 0) total += weights.get(edges[index - 1]?.id ?? "") ?? 0;
    arrivals.set(node, total);
  });
  return arrivals;
}

function overlayFromPath(
  network: Network,
  path: readonly string[],
  fewest: readonly string[] = [],
): RouteOverlay | null {
  const origin = path[0];
  const destination = path.at(-1);
  if (origin === undefined || destination === undefined) return null;
  const edges = pathEdges(network, path);
  const used = new Set(edges.map((edge) => edge.id));
  return {
    origin,
    destination,
    path: [...path],
    edges,
    arrivals: arrivalsAlong(network, path, edges),
    alternative: pathEdges(network, fewest)
      .map((edge) => edge.id)
      .filter((id) => !used.has(id)),
  };
}

export function routeOverlay(network: Network, report: RouteReport): RouteOverlay | null {
  if (!report.found) return null;
  return overlayFromPath(network, report.path, report.fewest_hops?.path ?? []);
}

export function attentionOverlay(network: Network, report: AttentionReport): RouteOverlay | null {
  return report.best ? overlayFromPath(network, report.best.path) : null;
}

/** Una fila del itinerario: un tramo de la ruta, con los minutos acumulados al llegar. */
export interface ItineraryRow {
  edgeId: string;
  from: string;
  to: string;
  minutes: number;
  arrival: number;
}

export function itinerary(network: Network, overlay: RouteOverlay): ItineraryRow[] {
  const byId = names(network);
  const weights = new Map(network.edges.map((edge) => [edge.id, edge.weight]));
  return overlay.edges.map((edge, index) => {
    const from = overlay.path[index] ?? "";
    const to = overlay.path[index + 1] ?? "";
    return {
      edgeId: edge.id,
      from: byId.get(from) ?? from,
      to: byId.get(to) ?? to,
      minutes: weights.get(edge.id) ?? 0,
      arrival: overlay.arrivals.get(to) ?? 0,
    };
  });
}

const placeNames = (network: Network, path: readonly string[]): string => {
  const byId = names(network);
  return path.map((id) => byId.get(id) ?? id).join(" → ");
};

/**
 * Frase principal para el operador, con nombres:
 * "De Base Norte a Centro: 15 min en 3 tramos, por Alameda y Bosque."
 */
export function routeSummary(network: Network, report: RouteReport): string {
  const byId = names(network);
  const origin = byId.get(report.origin) ?? report.origin;
  const destination = byId.get(report.destination) ?? report.destination;
  if (!report.found || report.total_cost === null || report.hops === null) {
    return `No hay ruta de ${origin} a ${destination}: ningún camino de la red los conecta en ese sentido.`;
  }
  if (report.hops === 0) return `${origin} es el punto de partida y el de llegada: 0 min.`;
  const stops = report.path.slice(1, -1).map((id) => byId.get(id) ?? id);
  const via = stops.length ? `, por ${joinList(stops)}` : ", directo";
  return `De ${origin} a ${destination}: ${formatMinutes(report.total_cost)} en ${plural(report.hops, "tramo", "tramos")}${via}.`;
}

/**
 * Comparación con el camino de menos tramos, o `null` si coinciden (o no hay ruta).
 * "El camino de menos tramos (Base Norte → Centro) tarda 30 min: esta ruta ahorra 15 min."
 */
export function fewestHopsComparison(network: Network, report: RouteReport): string | null {
  const fewest = report.fewest_hops;
  if (!report.found || !fewest || report.total_cost === null) return null;
  if (fewest.path.join() === report.path.join()) return null;
  const saving = fewest.cost - report.total_cost;
  const tail = saving > 0 ? `: esta ruta ahorra ${formatMinutes(saving)}.` : ".";
  return `El camino de menos tramos (${placeNames(network, fewest.path)}, ${plural(fewest.hops, "tramo", "tramos")}) tarda ${formatMinutes(fewest.cost)}${tail}`;
}

/** Cambia los ids de la red por sus nombres en un mensaje de la API ("B_OESTE" → "Base Oeste"). */
export function humanize(network: Network, message: string): string {
  const byId = names(network);
  const ids = [...byId.keys()].sort((a, b) => b.length - a.length);
  if (!ids.length) return message;
  const escaped = ids.map((id) => id.replace(/[.*+?^${}()|[\]\\-]/g, "\\$&"));
  const pattern = new RegExp(`(?<![A-Z0-9_-])(${escaped.join("|")})(?![A-Z0-9_-])`, "g");
  return message.replace(pattern, (id) => byId.get(id) ?? id);
}

/** "Enviar desde Base Sur (Marta): 20 min en 2 tramos." */
export function attentionSummary(network: Network, report: AttentionReport): string {
  const best = report.best;
  if (!best) return humanize(network, report.message);
  const byId = names(network);
  const who = best.technicians.map((t) => t.name);
  const people = who.length ? ` (${joinList(who)})` : "";
  return `Enviar desde ${byId.get(best.base) ?? best.base}${people}: ${formatMinutes(best.total_cost)} en ${plural(best.hops, "tramo", "tramos")}.`;
}

export interface AlternativeRow {
  id: string;
  name: string;
  minutes: number;
  hops: number;
}

export function alternativeRows(network: Network, report: AttentionReport): AlternativeRow[] {
  const byId = names(network);
  return report.alternatives.map((item) => ({
    id: item.base,
    name: byId.get(item.base) ?? item.base,
    minutes: item.total_cost,
    hops: item.hops,
  }));
}

const DIJKSTRA_ACTIONS: Record<string, string> = {
  pop: "Se fija (ya es el más rápido)",
  relax: "Mejora el tiempo",
  skip: "No mejora",
  stale: "Se descarta (dato viejo)",
};

export interface DijkstraTraceRow {
  key: string;
  base: string;
  step: number;
  action: string;
  node: string;
  minutes: string;
  from: string;
}

export function dijkstraTraceRows(
  network: Network,
  trace: RouteReport["trace"],
): DijkstraTraceRow[] {
  const byId = names(network);
  const nameOf = (id: unknown) => (typeof id === "string" ? (byId.get(id) ?? id) : "");
  return (trace ?? []).map((item, index) => {
    const cost = item.data.cost;
    return {
      key: String(index),
      base: nameOf(item.data.base),
      step: item.step,
      action: DIJKSTRA_ACTIONS[item.action] ?? item.action,
      node: nameOf(item.node),
      minutes: typeof cost === "number" ? formatMinutes(cost) : "",
      from: nameOf(item.data.from),
    };
  });
}
