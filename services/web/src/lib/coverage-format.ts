/** Transformaciones puras de la respuesta de cobertura (F2) a lo que muestra la consola. */
import { joinList, TYPE_LABELS } from "@/lib/network-format";
import type { CoverageReport, Network, NetworkNode, NodeType } from "@/lib/types";

const ACTION_LABELS: Record<string, string> = { enqueue: "Encola", visit: "Visita" };

export const nodesOfType = (network: Network, type: NodeType): NetworkNode[] =>
  network.nodes.filter((node) => node.type === type);

const names = (network: Network): Map<string, string> =>
  new Map(network.nodes.map((node) => [node.id, node.name]));

export interface ReachableRow {
  id: string;
  name: string;
  type: string;
  hops: number;
}

export function reachableRows(network: Network, report: CoverageReport): ReachableRow[] {
  const byId = names(network);
  return report.reachable.map((item) => ({
    id: item.node_id,
    name: byId.get(item.node_id) ?? item.node_id,
    type: TYPE_LABELS[item.type],
    hops: item.hops,
  }));
}

export function unreachableRows(
  network: Network,
  report: CoverageReport,
): { id: string; name: string }[] {
  const byId = names(network);
  return report.unreachable_zones.map((zone) => ({ id: zone, name: byId.get(zone) ?? zone }));
}

export interface TraceRow {
  step: number;
  action: string;
  node: string;
  hops: string;
  from: string;
}

export function traceRows(report: CoverageReport): TraceRow[] {
  return (report.trace ?? []).map((item) => {
    const hops = item.data.hops;
    const from = item.data.from;
    return {
      step: item.step,
      action: ACTION_LABELS[item.action] ?? item.action,
      node: item.node,
      hops: typeof hops === "number" ? String(hops) : "",
      from: typeof from === "string" ? from : "",
    };
  });
}

/** Mapa de tramos por nodo para resaltar la cobertura en el grafo. */
export interface CoverageOverlay {
  origin: string;
  hops: ReadonlyMap<string, number>;
  unreachable: ReadonlySet<string>;
}

export function coverageOverlay(report: CoverageReport): CoverageOverlay {
  return {
    origin: report.base,
    hops: new Map(report.reachable.map((item) => [item.node_id, item.hops])),
    unreachable: new Set(report.unreachable_zones),
  };
}

/**
 * Resumen en una frase para el operador, sin términos técnicos:
 * "Base Norte llega a 6 zonas y 1 base. Quedan sin cobertura Fuente e Isla."
 */
export function coverageSummary(network: Network, report: CoverageReport): string {
  const byId = names(network);
  const origin = byId.get(report.base) ?? report.base;
  const zones = report.reachable.filter((item) => item.type === "ZONE").length;
  const bases = report.reachable.length - zones;
  const reach: string[] = [];
  if (zones) reach.push(`${zones} ${zones === 1 ? "zona" : "zonas"}`);
  if (bases) reach.push(`${bases} ${bases === 1 ? "base" : "bases"}`);
  const first = reach.length
    ? `${origin} llega a ${joinList(reach)}.`
    : `${origin} no llega a ningún otro lugar.`;
  const missing = report.unreachable_zones.map((zone) => byId.get(zone) ?? zone);
  if (!missing.length) return `${first} Todas las zonas tienen cobertura.`;
  const verb = missing.length === 1 ? "Queda sin cobertura" : "Quedan sin cobertura";
  return `${first} ${verb} ${joinList(missing)}.`;
}
