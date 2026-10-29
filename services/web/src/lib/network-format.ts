/**
 * Transformaciones puras entre la red del contrato y lo que muestra o envía la consola.
 * Sin React ni HTTP. Las reglas de negocio (formato de ids, pesos, duplicados) las valida
 * network-service; aquí solo se da forma a los datos (equivalente a console/network_format.py).
 */
import { ApiError } from "@/lib/api";
import type {
  ImportPayload,
  Network,
  NetworkEdge,
  NetworkNode,
  NodeInput,
  NodeType,
  Technician,
} from "@/lib/types";

export const TYPE_LABELS: Record<NodeType, string> = { BASE: "Base", ZONE: "Zona" };
export const WEIGHT_MAX_MINUTES = 1440;
const ID_MAX = 32;

export class FormInputError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "FormInputError";
  }
}

/** Opciones para elegir un lugar por su nombre; el id solo aparece si hay nombres repetidos. */
export function nodeOptions(nodes: NetworkNode[]): { value: string; label: string }[] {
  const counts = new Map<string, number>();
  for (const node of nodes) counts.set(node.name, (counts.get(node.name) ?? 0) + 1);
  return nodes.map((node) => ({
    value: node.id,
    label: (counts.get(node.name) ?? 0) > 1 ? `${node.name} (${node.id})` : node.name,
  }));
}

/** "A", "A y B", "A, B y C"; "e" antes de sonido "i" ("Fuente e Isla", pero "y hielo"). */
export function joinList(items: string[]): string {
  if (items.length <= 1) return items.join("");
  const last = items.at(-1) ?? "";
  const conjunction = /^h?[ií](?![aeouáéóú])/i.test(last) ? "e" : "y";
  return `${items.slice(0, -1).join(", ")} ${conjunction} ${last}`;
}

export const freeTechnicians = (node: NetworkNode): number =>
  node.technicians.filter((t) => t.available).length;

export function plural(count: number, one: string, many: string): string {
  return `${count} ${count === 1 ? one : many}`;
}

export function formatMinutes(weight: number): string {
  return `${Number.isInteger(weight) ? weight : Number(weight.toFixed(2))} min`;
}

export function weightInRange(weight: number): boolean {
  return Number.isFinite(weight) && weight > 0 && weight <= WEIGHT_MAX_MINUTES;
}

/** Texto en mayúsculas, sin tildes y con '_' en lugar de espacios: "Estación Sur" → "ESTACION_SUR". */
function slug(text: string): string {
  return text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "");
}

/**
 * Id sugerido a partir del nombre, para que nadie tenga que inventarlo: "Base Este" → "B_ESTE",
 * "Estación Sur" → "Z_ESTACION_SUR". Si ya existe, agrega "_2", "_3"…
 */
export function suggestNodeId(type: NodeType, name: string, taken: Iterable<string>): string {
  const prefix = type === "BASE" ? "B" : "Z";
  const word = type === "BASE" ? /^BASE_/ : /^ZONA_/;
  const core = slug(name).replace(word, "");
  if (!core) return "";
  const used = new Set(taken);
  const base = `${prefix}_${core}`.slice(0, ID_MAX);
  if (!used.has(base)) return base;
  for (let n = 2; ; n++) {
    const candidate = `${base.slice(0, ID_MAX - String(n).length - 1)}_${n}`;
    if (!used.has(candidate)) return candidate;
  }
}

/** Siguiente id libre con el prefijo dado: E01…E09 → "E10". */
export function nextId(prefix: string, taken: Iterable<string>): string {
  const pattern = new RegExp(`^${prefix}(\\d+)$`);
  let max = 0;
  for (const id of taken) {
    const match = pattern.exec(id);
    if (match) max = Math.max(max, Number(match[1]));
  }
  return `${prefix}${String(max + 1).padStart(2, "0")}`;
}

export interface TechnicianDraft {
  name: string;
  available: boolean;
}

/** Cuerpo de `POST /api/v1/nodes`. Los técnicos reciben ids libres (T01, T02…); las zonas no llevan. */
export function nodePayload(
  nodeId: string,
  type: NodeType,
  name: string,
  technicians: TechnicianDraft[],
  takenTechnicianIds: Iterable<string>,
): NodeInput {
  if (!name.trim()) throw new FormInputError("Escriba el nombre.");
  if (!nodeId.trim()) throw new FormInputError("Escriba un identificador.");
  const payload: NodeInput = { id: nodeId.trim(), type, name: name.trim() };
  if (type !== "BASE") return payload;
  const taken = new Set(takenTechnicianIds);
  const list: Technician[] = [];
  for (const technician of technicians) {
    if (!technician.name.trim()) continue;
    const id = nextId("T", taken);
    taken.add(id);
    list.push({ id, name: technician.name.trim(), available: technician.available });
  }
  payload.technicians = list;
  return payload;
}

export function edgePayload(
  edgeId: string,
  source: string,
  target: string,
  weight: number,
  bidirectional: boolean,
): NetworkEdge {
  return { id: edgeId.trim(), source, target, weight, bidirectional };
}

export function parseNetworkFile(content: string, replace: boolean): ImportPayload {
  let data: unknown;
  try {
    data = JSON.parse(content);
  } catch {
    throw new FormInputError("El archivo no es un JSON válido.");
  }
  if (
    typeof data !== "object" ||
    data === null ||
    !Array.isArray((data as { nodes?: unknown }).nodes) ||
    !Array.isArray((data as { edges?: unknown }).edges)
  ) {
    throw new FormInputError("El archivo debe tener las listas 'nodes' y 'edges'.");
  }
  const { nodes, edges } = data as { nodes: unknown[]; edges: unknown[] };
  return { nodes, edges, replace };
}

/** Mensaje legible del contrato; para VALIDATION_ERROR agrega los campos afectados. */
export function errorText(error: Pick<ApiError, "message" | "details">): string {
  const errors = Array.isArray(error.details.errors) ? (error.details.errors as unknown[]) : [];
  const fields = errors
    .filter(
      (item): item is { field: unknown } =>
        typeof item === "object" && item !== null && "field" in item,
    )
    .map((item) => String(item.field).replace(/^body\./, ""));
  let location = "";
  const { section, index } = error.details;
  if (section !== undefined && index !== undefined) {
    const kind = section === "nodes" ? "nodo" : "conexión";
    location = ` (archivo: ${kind} #${Number(index) + 1})`;
  }
  const suffix = fields.length ? ` Campos: ${fields.join(", ")}.` : "";
  return `${error.message}${location}${suffix}`;
}

/** Texto para cualquier error que llegue a la interfaz (del contrato, del formulario u otro). */
export function describeError(error: unknown): string {
  if (error instanceof ApiError) return errorText(error);
  if (error instanceof Error) return error.message;
  return "Ocurrió un error inesperado.";
}

export interface Kpi {
  value: number;
  label: string;
  help: string;
}

export function networkKpis(network: Network): Kpi[] {
  const bases = network.nodes.filter((n) => n.type === "BASE");
  const zones = network.nodes.filter((n) => n.type === "ZONE");
  const linked = new Set(network.edges.flatMap((e) => [e.source, e.target]));
  const withFree = bases.filter((b) => freeTechnicians(b) > 0).length;
  const oneWay = network.edges.filter((e) => !e.bidirectional).length;
  const isolated = zones.filter((z) => !linked.has(z.id)).length;
  return [
    { value: bases.length, label: "Bases", help: `${withFree} con técnico libre` },
    { value: zones.length, label: "Zonas", help: `${zones.length - isolated} con trayectos` },
    { value: network.edges.length, label: "Trayectos", help: `${oneWay} de un solo sentido` },
    {
      value: isolated,
      label: "Zonas sin conexión",
      help: isolated ? "ninguna base llega" : "todas conectadas",
    },
  ];
}

export interface NodeLink {
  arrow: "↔" | "→" | "←";
  other: string;
  minutes: number;
  edgeId: string;
}

export interface NodeCardData {
  name: string;
  typeLabel: string;
  id: string;
  isBase: boolean;
  technicians: Technician[];
  links: NodeLink[];
  note: string;
}

export function nodeCard(network: Network, nodeId: string): NodeCardData | null {
  const byId = new Map(network.nodes.map((n) => [n.id, n]));
  const node = byId.get(nodeId);
  if (!node) return null;
  const links: NodeLink[] = [];
  for (const edge of network.edges) {
    if (edge.source !== nodeId && edge.target !== nodeId) continue;
    const outgoing = edge.source === nodeId;
    const other = byId.get(outgoing ? edge.target : edge.source);
    links.push({
      arrow: edge.bidirectional ? "↔" : outgoing ? "→" : "←",
      other: other?.name ?? "?",
      minutes: edge.weight,
      edgeId: edge.id,
    });
  }
  const isBase = node.type === "BASE";
  let note = "";
  if (!links.length) {
    note = isBase
      ? "Base sin trayectos: no puede llegar a ninguna zona."
      : "Sin trayectos registrados: ninguna base puede llegar a esta zona.";
  } else if (isBase && freeTechnicians(node) === 0) {
    note = "Base sin técnicos disponibles: llega a sus zonas, pero no puede atenderlas.";
  }
  return {
    name: node.name,
    typeLabel: TYPE_LABELS[node.type],
    id: node.id,
    isBase,
    technicians: node.technicians,
    links,
    note,
  };
}

export function technicianSummary(node: NetworkNode): string {
  return node.technicians.length
    ? node.technicians.map((t) => `${t.name} (${t.id}) ${t.available ? "✔" : "✘"}`).join(", ")
    : "—";
}

export const senseLabel = (edge: NetworkEdge): string =>
  edge.bidirectional ? "↔ ambos sentidos" : "→ solo ida";
