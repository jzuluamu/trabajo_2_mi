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
