/**
 * Cliente del BFF (`/bff`). El navegador nunca ve la API key: la sesión va en una cookie HttpOnly.
 * Los errores llegan con el formato del contrato `{code, message, details}` y se lanzan como ApiError.
 */
import type {
  CoverageReport,
  ImportPayload,
  ImportSummary,
  Network,
  NetworkEdge,
  NetworkNode,
  NodeInput,
  Role,
  ServiceHealth,
} from "@/lib/types";

export class ApiError extends Error {
  constructor(
    readonly code: string,
    message: string,
    readonly status: number | null = null,
    readonly details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

async function toError(response: Response): Promise<ApiError> {
  let body: unknown;
  try {
    body = await response.json();
  } catch {
    body = null;
  }
  const data = isRecord(body) ? body : {};
  return new ApiError(
    typeof data.code === "string" ? data.code : `HTTP_${response.status}`,
    typeof data.message === "string" ? data.message : "Respuesta inesperada del servicio.",
    response.status,
    isRecord(data.details) ? data.details : {},
  );
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json", "X-ServicioCerca": "1" };
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let response: Response;
  try {
    response = await fetch(`/bff${path}`, {
      method,
      headers,
      credentials: "same-origin",
      body: body === undefined ? null : JSON.stringify(body),
    });
  } catch {
    throw new ApiError("SERVICE_UNAVAILABLE", "No fue posible contactar la consola.");
  }
  if (response.status === 204) return undefined as T;
  if (!response.ok) throw await toError(response);
  return (await response.json()) as T;
}

const id = (value: string): string => encodeURIComponent(value);

export const api = {
  health: () => request<{ services: ServiceHealth[] }>("GET", "/health"),
  session: () => request<{ role: Role | null }>("GET", "/session"),
  login: (apiKey: string) => request<{ role: Role }>("POST", "/session", { api_key: apiKey }),
  logout: () => request<undefined>("DELETE", "/session"),
  network: () => request<Network>("GET", "/api/network/network"),
  createNode: (node: NodeInput) => request<NetworkNode>("POST", "/api/network/nodes", node),
  createEdge: (edge: NetworkEdge) => request<NetworkEdge>("POST", "/api/network/edges", edge),
  deleteNode: (nodeId: string) => request<undefined>("DELETE", `/api/network/nodes/${id(nodeId)}`),
  deleteEdge: (edgeId: string) => request<undefined>("DELETE", `/api/network/edges/${id(edgeId)}`),
  importNetwork: (payload: ImportPayload) =>
    request<ImportSummary>("POST", "/api/network/network/import", payload),
  coverage: (base: string, zone: string | null, trace: boolean) => {
    const params = new URLSearchParams({ base, trace: String(trace) });
    if (zone) params.set("zone", zone);
    return request<CoverageReport>("GET", `/api/routing/coverage?${params.toString()}`);
  },
};
