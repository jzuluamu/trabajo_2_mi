import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { createApp, CSRF_HEADER, MAX_BODY_BYTES, SESSION_COOKIE } from "../../server/app.js";
import type { Config } from "../../server/config.js";
import { SessionStore } from "../../server/sessions.js";
import { FakeUpstream } from "./fake-upstream.js";

const staticDir = mkdtempSync(join(tmpdir(), "web-static-"));
writeFileSync(join(staticDir, "index.html"), "<!doctype html><title>Consola</title>");
writeFileSync(join(staticDir, "app.js"), "console.log('ok')");

const config: Config = {
  networkServiceUrl: "http://network:8001",
  routingServiceUrl: "http://routing:8002",
  port: 8080,
  requestTimeoutMs: 1000,
  sessionTtlMinutes: 60,
  cookieSecure: false,
  staticDir,
};

const CSRF = { [CSRF_HEADER]: "1" };

function setup() {
  const upstream = new FakeUpstream();
  const sessions = new SessionStore(60_000);
  const app = createApp({ config, sessions, fetch: upstream.fetch });
  return { app, upstream, sessions };
}

function sessionCookie(response: Response): string {
  const header = response.headers.get("set-cookie") ?? "";
  const value = new RegExp(`${SESSION_COOKIE}=([^;]+)`).exec(header)?.[1];
  if (!value) throw new Error("sin cookie de sesión");
  return `${SESSION_COOKIE}=${value}`;
}

async function login(app: ReturnType<typeof setup>["app"], key = "coord-key-0123456789") {
  const response = await app.request("/bff/session", {
    method: "POST",
    headers: { ...CSRF, "Content-Type": "application/json" },
    body: JSON.stringify({ api_key: key }),
  });
  return { response, cookie: sessionCookie(response) };
}

describe("health", () => {
  it("responde healthz para el healthcheck de Docker", async () => {
    const { app } = setup();
    const response = await app.request("/healthz");
    expect(await response.json()).toEqual({ status: "ok" });
  });

  it("informa cada servicio como operativo o caído sin romperse", async () => {
    const { app, upstream } = setup();
    upstream.down.add("routing:8002");
    const response = await app.request("/bff/health");
    expect(await response.json()).toEqual({
      services: [
        { name: "network-service", status: "ok" },
        { name: "routing-service", status: "down" },
      ],
    });
  });

  it("marca como caído un servicio que responde con error", async () => {
    const upstream = new FakeUpstream();
    const app = createApp({
      config,
      sessions: new SessionStore(60_000),
      fetch: async (input, init) =>
        (input instanceof Request ? input.url : input.toString()).includes("network")
          ? new Response("", { status: 500 })
          : upstream.fetch(input, init),
    });
    const body = (await (await app.request("/bff/health")).json()) as {
      services: { status: string }[];
    };
    expect(body.services.map((s) => s.status)).toEqual(["down", "ok"]);
  });
});

describe("sesión", () => {
  it("inicia sesión: guarda la clave en el servidor y entrega solo una cookie HttpOnly", async () => {
    const { app, upstream } = setup();
    const { response } = await login(app);
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ role: "coordinator" });
    const cookie = response.headers.get("set-cookie") ?? "";
    expect(cookie).toContain("HttpOnly");
    expect(cookie).toContain("SameSite=Strict");
    expect(cookie).not.toContain("coord-key");
    expect(upstream.calls[0]?.url).toBe("http://network:8001/api/v1/auth/whoami");
  });

  it("consulta la sesión vigente", async () => {
    const { app } = setup();
    const { cookie } = await login(app, "oper-key-0123456789");
    const response = await app.request("/bff/session", { headers: { Cookie: cookie } });
    expect(await response.json()).toEqual({ role: "operator" });
  });

  it("sin sesión responde role null (no es un error)", async () => {
    const { app } = setup();
    const response = await app.request("/bff/session");
    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ role: null });
  });

  it("una clave inválida devuelve el mensaje del contrato y no crea sesión", async () => {
    const { app, sessions } = setup();
    const response = await app.request("/bff/session", {
      method: "POST",
      headers: CSRF,
      body: JSON.stringify({ api_key: "nope" }),
    });
    expect(response.status).toBe(401);
    expect(await response.json()).toMatchObject({ message: "API key inválida." });
    expect(sessions.size).toBe(0);
  });

  it("rechaza la clave interna como usuario de la consola", async () => {
    const { app, sessions } = setup();
    const response = await app.request("/bff/session", {
      method: "POST",
      headers: CSRF,
      body: JSON.stringify({ api_key: "internal-key-0123456789" }),
    });
    expect(response.status).toBe(403);
    expect(await response.json()).toMatchObject({
      message: "Esta clave no corresponde a un usuario de la consola.",
    });
    expect(sessions.size).toBe(0);
  });

  it.each([["{}"], ['{"api_key": "   "}'], ['{"api_key": 5}'], ["no es json"]])(
    "valida el cuerpo del inicio de sesión: %s",
    async (body) => {
      const { app } = setup();
      const response = await app.request("/bff/session", { method: "POST", headers: CSRF, body });
      expect(response.status).toBe(422);
      expect(await response.json()).toMatchObject({
        code: "VALIDATION_ERROR",
        message: "Ingrese su API key.",
      });
    },
  );

  it("si network-service no responde, informa el servicio caído", async () => {
    const { app, upstream } = setup();
    upstream.down.add("network:8001");
    const response = await app.request("/bff/session", {
      method: "POST",
      headers: CSRF,
      body: JSON.stringify({ api_key: "coord-key-0123456789" }),
    });
    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      code: "SERVICE_UNAVAILABLE",
      message: "No fue posible contactar network-service.",
      details: {},
    });
  });

  it("un nuevo inicio de sesión invalida el id anterior", async () => {
    const { app } = setup();
    const first = await login(app);
    const second = await app.request("/bff/session", {
      method: "POST",
      headers: { ...CSRF, Cookie: first.cookie },
      body: JSON.stringify({ api_key: "oper-key-0123456789" }),
    });
    expect(sessionCookie(second)).not.toBe(first.cookie);
    const old = await app.request("/bff/session", { headers: { Cookie: first.cookie } });
    expect(await old.json()).toEqual({ role: null });
  });

  it("cierra sesión y borra la cookie", async () => {
    const { app } = setup();
    const { cookie } = await login(app);
    const response = await app.request("/bff/session", {
      method: "DELETE",
      headers: { ...CSRF, Cookie: cookie },
    });
    expect(response.status).toBe(204);
    expect(response.headers.get("set-cookie")).toContain(`${SESSION_COOKIE}=;`);
    const after = await app.request("/bff/session", { headers: { Cookie: cookie } });
    expect(await after.json()).toEqual({ role: null });
  });

  it("emite la cookie con Secure cuando COOKIE_SECURE está activo", async () => {
    const upstream = new FakeUpstream();
    const app = createApp({
      config: { ...config, cookieSecure: true },
      sessions: new SessionStore(60_000),
      fetch: upstream.fetch,
    });
    const { response } = await login(app);
    expect(response.headers.get("set-cookie")).toContain("Secure");
  });
});

describe("CSRF", () => {
  it("rechaza un método que modifica sin el encabezado propio", async () => {
    const { app } = setup();
    const { cookie } = await login(app);
    const response = await app.request("/bff/api/network/nodes/B_X", {
      method: "DELETE",
      headers: { Cookie: cookie },
    });
    expect(response.status).toBe(403);
    expect(await response.json()).toMatchObject({
      code: "FORBIDDEN",
      message: "Solicitud rechazada.",
    });
  });
});

describe("proxy", () => {
  it("reenvía con la X-API-Key de la sesión y conserva la consulta", async () => {
    const { app, upstream } = setup();
    const { cookie } = await login(app, "oper-key-0123456789");
    const response = await app.request("/bff/api/routing/coverage?base=B_NORTE&trace=true", {
      headers: { Cookie: cookie },
    });
    expect(await response.json()).toEqual({ base: "B_NORTE" });
    const call = upstream.calls.at(-1)!;
    expect(call.url).toBe("http://routing:8002/api/v1/coverage?base=B_NORTE&trace=true");
    expect(call.apiKey).toBe("oper-key-0123456789");
  });

  it("reenvía el cuerpo JSON y el error del contrato tal cual", async () => {
    const { app, upstream } = setup();
    const { cookie } = await login(app);
    const body = JSON.stringify({ id: "E10", source: "A", target: "B", weight: -5 });
    const response = await app.request("/bff/api/network/edges", {
      method: "POST",
      headers: { ...CSRF, Cookie: cookie },
      body,
    });
    expect(response.status).toBe(422);
    expect(await response.json()).toMatchObject({ code: "INVALID_WEIGHT" });
    expect(upstream.calls.at(-1)?.body).toBe(body);
  });

  it("propaga 204 sin cuerpo", async () => {
    const { app } = setup();
    const { cookie } = await login(app);
    const response = await app.request("/bff/api/network/nodes/B_ESTE", {
      method: "DELETE",
      headers: { ...CSRF, Cookie: cookie },
    });
    expect(response.status).toBe(204);
    expect(await response.text()).toBe("");
  });

  it("sin sesión responde 401 y no contacta al servicio", async () => {
    const { app, upstream } = setup();
    const response = await app.request("/bff/api/network/network");
    expect(response.status).toBe(401);
    expect(upstream.calls).toHaveLength(0);
  });

  it.each([
    ["GET", "/bff/api/network/auth/whoami"],
    ["DELETE", "/bff/api/network/network"],
    ["GET", "/bff/api/network/nodes/..%2F..%2Fhealth"],
    ["GET", "/bff/api/otro/network"],
    ["GET", "/bff/api/routing/coverage/extra"],
    ["GET", "/bff/desconocido"],
  ])("solo permite rutas del contrato: %s %s", async (method, path) => {
    const { app, upstream } = setup();
    const { cookie } = await login(app);
    const before = upstream.calls.length;
    const response = await app.request(path, { method, headers: { ...CSRF, Cookie: cookie } });
    expect(response.status).toBe(404);
    expect(await response.json()).toMatchObject({ code: "NOT_FOUND" });
    expect(upstream.calls).toHaveLength(before);
  });

  it("si el servicio no responde, devuelve 503 con mensaje legible", async () => {
    const { app, upstream } = setup();
    const { cookie } = await login(app);
    upstream.down.add("routing:8002");
    const response = await app.request("/bff/api/routing/coverage?base=B_NORTE", {
      headers: { Cookie: cookie },
    });
    expect(response.status).toBe(503);
    expect(await response.json()).toMatchObject({
      message: "No fue posible contactar routing-service.",
    });
  });

  it("una respuesta que no es JSON se informa como 502 genérico", async () => {
    const { app } = setup();
    const { cookie } = await login(app);
    const response = await app.request("/bff/api/network/edges", { headers: { Cookie: cookie } });
    expect(response.status).toBe(502);
    expect(await response.json()).toMatchObject({ code: "BAD_GATEWAY" });
  });

  it("si el servicio rechaza la clave, cierra la sesión", async () => {
    const { app, upstream } = setup();
    const { cookie } = await login(app);
    upstream.revoked = true;
    const response = await app.request("/bff/api/network/network", { headers: { Cookie: cookie } });
    expect(response.status).toBe(401);
    upstream.revoked = false;
    const session = await app.request("/bff/session", { headers: { Cookie: cookie } });
    expect(await session.json()).toEqual({ role: null });
  });

  it("limita el tamaño del cuerpo", async () => {
    const { app } = setup();
    const { cookie } = await login(app);
    const response = await app.request("/bff/api/network/network/import", {
      method: "POST",
      headers: { ...CSRF, Cookie: cookie, "Content-Length": String(MAX_BODY_BYTES + 1) },
      body: "x".repeat(MAX_BODY_BYTES + 1),
    });
    expect(response.status).toBe(413);
    expect(await response.json()).toMatchObject({ code: "PAYLOAD_TOO_LARGE" });
  });
});

describe("estáticos y cabeceras", () => {
  it("sirve la SPA con CSP estricta y sin caché en /bff", async () => {
    const { app } = setup();
    const page = await app.request("/");
    expect(await page.text()).toContain("<title>Consola</title>");
    const csp = page.headers.get("content-security-policy") ?? "";
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("script-src 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(page.headers.get("x-content-type-options")).toBe("nosniff");
    const api = await app.request("/bff/health");
    expect(api.headers.get("cache-control")).toBe("no-store");
  });

  it("sirve archivos y devuelve index.html para rutas de la SPA", async () => {
    const { app } = setup();
    expect(await (await app.request("/app.js")).text()).toContain("console.log");
    expect(await (await app.request("/cobertura")).text()).toContain("<title>Consola</title>");
  });

  it("un error inesperado responde 500 genérico sin filtrar detalles", async () => {
    vi.spyOn(console, "error").mockImplementation(() => undefined);
    const broken = createApp({
      config,
      sessions: {
        get: () => {
          throw new Error("secreto interno");
        },
      } as unknown as SessionStore,
    });
    const response = await broken.request("/bff/session");
    expect(response.status).toBe(500);
    const body = await response.text();
    expect(body).not.toContain("secreto");
    expect(JSON.parse(body)).toMatchObject({ code: "INTERNAL_ERROR" });
  });
});
