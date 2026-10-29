/** network-service y routing-service falsos para el BFF: solo la forma de las respuestas. */
export const KEYS: Record<string, string> = {
  "coord-key-0123456789": "coordinator",
  "oper-key-0123456789": "operator",
  "internal-key-0123456789": "internal",
};

export interface Call {
  url: string;
  method: string;
  apiKey: string | null;
  body: string | null;
}

const json = (status: number, body: unknown): Response =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

export class FakeUpstream {
  calls: Call[] = [];
  down = new Set<string>();
  revoked = false;

  readonly fetch = (input: string | URL | Request, init?: RequestInit): Promise<Response> => {
    const url = new URL(input instanceof Request ? input.url : input);
    const response = this.handle(url, init);
    return response ? Promise.resolve(response) : Promise.reject(new TypeError("fetch failed"));
  };

  /** Respuesta del servicio falso, o `null` si el servicio está caído (fallo de red). */
  private handle(url: URL, init?: RequestInit): Response | null {
    const headers = new Headers(init?.headers);
    const body = typeof init?.body === "string" ? init.body : null;
    const call = {
      url: url.toString(),
      method: init?.method ?? "GET",
      apiKey: headers.get("X-API-Key"),
      body,
    };
    this.calls.push(call);
    if (this.down.has(url.host)) return null;
    if (url.pathname === "/health") return json(200, { status: "ok" });
    const role = call.apiKey ? KEYS[call.apiKey] : undefined;
    if (!role || this.revoked) {
      return json(401, { code: "UNAUTHENTICATED", message: "API key inválida.", details: {} });
    }
    if (url.pathname === "/api/v1/auth/whoami") return json(200, { role });
    if (url.pathname === "/api/v1/network") return json(200, { nodes: [], edges: [] });
    if (url.pathname.startsWith("/api/v1/nodes/") && call.method === "DELETE") {
      return new Response(null, { status: 204 });
    }
    if (url.pathname === "/api/v1/edges" && call.method === "POST") {
      return json(422, { code: "INVALID_WEIGHT", message: "Peso inválido.", details: {} });
    }
    if (url.pathname === "/api/v1/coverage")
      return json(200, { base: url.searchParams.get("base") });
    if (url.pathname === "/api/v1/edges") return new Response("<html>oops</html>", { status: 200 });
    return json(404, { code: "NOT_FOUND", message: "No existe.", details: {} });
  }
}
