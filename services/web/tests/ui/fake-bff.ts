/**
 * BFF falso para las pruebas de interfaz: reproduce la forma de las respuestas y de los errores
 * de docs/03-api.md, sin reimplementar todas las reglas (como tests/fake_network.py en la consola).
 */
import { COVERAGE_NORTE, DEMO } from "../fixtures";
import type {
  CoverageReport,
  Network,
  NetworkEdge,
  NodeInput,
  Role,
  ServiceHealth,
} from "@/lib/types";

interface ErrorReply {
  status: number;
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

interface ImportBody {
  nodes: NodeInput[];
  edges: NetworkEdge[];
  replace: boolean;
}

export interface Request {
  method: string;
  path: string;
  body: unknown;
}

const reply = (status: number, body?: unknown): Response =>
  body === undefined
    ? new Response(null, { status })
    : new Response(JSON.stringify(body), {
        status,
        headers: { "Content-Type": "application/json" },
      });

const error = ({ status, code, message, details = {} }: ErrorReply): Response =>
  reply(status, { code, message, details });

export class FakeBff {
  role: Role | null = null;
  network: Network = structuredClone(DEMO);
  services: ServiceHealth[] = [
    { name: "network-service", status: "ok" },
    { name: "routing-service", status: "ok" },
  ];
  requests: Request[] = [];
  /** Error que responde la próxima petición `MÉTODO /ruta` (sin la consulta). */
  failures = new Map<string, ErrorReply>();
  offline = false;

  constructor({ role = null, empty = false }: { role?: Role | null; empty?: boolean } = {}) {
    this.role = role;
    if (empty) this.network = { nodes: [], edges: [] };
  }

  install(): this {
    vi.spyOn(globalThis, "fetch").mockImplementation((input, init) => {
      const url = new URL(input instanceof Request ? input.url : String(input), "http://localhost");
      const method = init?.method ?? "GET";
      const body = typeof init?.body === "string" ? (JSON.parse(init.body) as unknown) : null;
      this.requests.push({ method, path: url.pathname + url.search, body });
      if (this.offline) return Promise.reject(new TypeError("Failed to fetch"));
      return Promise.resolve(this.handle(method, url, body));
    });
    return this;
  }

  last(method: string, prefix: string): Request | undefined {
    return this.requests.filter((r) => r.method === method && r.path.startsWith(prefix)).at(-1);
  }

  private handle(method: string, url: URL, body: unknown): Response {
    const path = url.pathname.replace(/^\/bff/, "");
    const failure = this.failures.get(`${method} ${path}`);
    if (failure) {
      this.failures.delete(`${method} ${path}`);
      return error(failure);
    }
    if (path === "/health") return reply(200, { services: this.services });
    if (path === "/session") return this.session(method, body);
    if (!this.role)
      return error({
        status: 401,
        code: "UNAUTHENTICATED",
        message: "Inicie sesión con su API key.",
      });
    if (path === "/api/network/network") return reply(200, this.network);
    if (path === "/api/network/nodes" && method === "POST")
      return this.createNode(body as NodeInput);
    if (path === "/api/network/edges" && method === "POST")
      return this.createEdge(body as NetworkEdge);
    if (path.startsWith("/api/network/nodes/"))
      return this.deleteNode(decodeURIComponent(path.split("/").at(-1)!));
    if (path.startsWith("/api/network/edges/")) {
      const id = decodeURIComponent(path.split("/").at(-1)!);
      this.network.edges = this.network.edges.filter((e) => e.id !== id);
      return reply(204);
    }
    if (path === "/api/network/network/import") return this.importNetwork(body as ImportBody);
    if (path === "/api/routing/coverage") return this.coverage(url.searchParams);
    return error({ status: 404, code: "NOT_FOUND", message: "Recurso no encontrado." });
  }

  private session(method: string, body: unknown): Response {
    if (method === "DELETE") {
      this.role = null;
      return reply(204);
    }
    if (method === "GET") {
      return reply(200, { role: this.role });
    }
    const key = (body as { api_key: string }).api_key;
    const roles: Record<string, Role> = { coord: "coordinator", oper: "operator" };
    if (key === "internal") {
      return error({
        status: 403,
        code: "FORBIDDEN",
        message: "Esta clave no corresponde a un usuario de la consola.",
      });
    }
    const role = roles[key];
    if (!role) return error({ status: 401, code: "UNAUTHENTICATED", message: "API key inválida." });
    this.role = role;
    return reply(200, { role });
  }

  private createNode(node: NodeInput): Response {
    if (this.network.nodes.some((n) => n.id === node.id)) {
      return error({
        status: 409,
        code: "DUPLICATE_ID",
        message: `Ya existe un nodo con id '${node.id}'.`,
      });
    }
    const created = { ...node, technicians: node.technicians ?? [] };
    this.network.nodes.push(created);
    return reply(201, created);
  }

  private createEdge(edge: NetworkEdge): Response {
    if (!(edge.weight > 0 && edge.weight <= 1440)) {
      return error({
        status: 422,
        code: "INVALID_WEIGHT",
        message: `El peso de la conexión '${edge.id}' debe ser mayor que 0 y menor o igual a 1440 minutos.`,
      });
    }
    this.network.edges.push(edge);
    return reply(201, edge);
  }

  private deleteNode(id: string): Response {
    const inUse = this.network.edges
      .filter((e) => e.source === id || e.target === id)
      .map((e) => e.id);
    if (inUse.length) {
      return error({
        status: 409,
        code: "NODE_IN_USE",
        message: `El nodo '${id}' tiene conexiones; elimínelas primero.`,
        details: { edge_ids: inUse },
      });
    }
    this.network.nodes = this.network.nodes.filter((n) => n.id !== id);
    return reply(204);
  }

  private importNetwork(payload: ImportBody): Response {
    const nodes = payload.nodes.map((n) => ({ ...n, technicians: n.technicians ?? [] }));
    this.network = payload.replace
      ? { nodes, edges: payload.edges }
      : {
          nodes: [...this.network.nodes, ...nodes],
          edges: [...this.network.edges, ...payload.edges],
        };
    return reply(201, { nodes: payload.nodes.length, edges: payload.edges.length });
  }

  private coverage(params: URLSearchParams): Response {
    const base = params.get("base");
    if (base !== "B_NORTE") {
      return error({
        status: 404,
        code: "ORIGIN_NOT_FOUND",
        message: `La base '${base ?? ""}' no existe.`,
      });
    }
    const zone = params.get("zone");
    const report: CoverageReport = structuredClone(COVERAGE_NORTE);
    if (zone) {
      const hops = report.reachable.find((r) => r.node_id === zone)?.hops ?? null;
      report.zone = {
        id: zone,
        covered: hops !== null,
        hops,
        message:
          hops !== null
            ? `${zone} está cubierta desde B_NORTE (${hops} tramo${hops === 1 ? "" : "s"}).`
            : `${zone} no tiene conexión desde B_NORTE.`,
      };
    }
    if (params.get("trace") === "true") {
      report.trace = [
        { step: 1, action: "visit", node: "B_NORTE", data: { hops: 0 } },
        { step: 2, action: "enqueue", node: "Z_ALAMEDA", data: { hops: 1, from: "B_NORTE" } },
      ];
    }
    return reply(200, report);
  }
}
