/** Tipos del contrato HTTP (docs/03-api.md) tal como los entrega el BFF. */

export type Role = "coordinator" | "operator";
export type NodeType = "BASE" | "ZONE";

export interface Technician {
  id: string;
  name: string;
  available: boolean;
}

export interface NetworkNode {
  id: string;
  type: NodeType;
  name: string;
  technicians: Technician[];
}

export interface NetworkEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  bidirectional: boolean;
}

export interface Network {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface NodeInput {
  id: string;
  type: NodeType;
  name: string;
  technicians?: Technician[];
}

export interface ImportPayload {
  nodes: unknown[];
  edges: unknown[];
  replace: boolean;
}

export interface ImportSummary {
  nodes: number;
  edges: number;
}

export interface ReachableNode {
  node_id: string;
  type: NodeType;
  hops: number;
}

export interface ZoneCheck {
  id: string;
  covered: boolean;
  hops: number | null;
  message: string;
}

export interface TraceStep {
  step: number;
  action: string;
  node: string;
  data: Record<string, unknown>;
}

export interface CoverageReport {
  base: string;
  reachable: ReachableNode[];
  unreachable_zones: string[];
  zone: ZoneCheck | null;
  trace: TraceStep[] | null;
}

export interface ServiceHealth {
  name: string;
  status: "ok" | "down";
}

/** Tramo de una ruta: la conexión recorrida en el sentido del viaje (`from` → `to`). */
export interface RouteLeg {
  edge_id: string;
  from: string;
  to: string;
  weight: number;
}

export interface FewestHops {
  path: string[];
  hops: number;
  cost: number;
}

export interface RouteReport {
  found: boolean;
  origin: string;
  destination: string;
  path: string[];
  total_cost: number | null;
  hops: number | null;
  legs: RouteLeg[];
  fewest_hops: FewestHops | null;
  message: string;
  trace: TraceStep[] | null;
}

export interface BestBase {
  base: string;
  technicians: { id: string; name: string }[];
  path: string[];
  total_cost: number;
  hops: number;
}

export interface AlternativeBase {
  base: string;
  total_cost: number;
  hops: number;
}

export interface AttentionReport {
  zone: string;
  found: boolean;
  best: BestBase | null;
  alternatives: AlternativeBase[];
  message: string;
  trace: TraceStep[] | null;
}
