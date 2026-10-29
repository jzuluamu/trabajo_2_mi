/**
 * BFF de la consola web (ADR 0007): sirve la SPA y hace de proxy hacia los servicios.
 *
 * - Inicio de sesión: valida la API key con `/auth/whoami` y la guarda en la sesión del servidor;
 *   el navegador solo recibe una cookie `HttpOnly; SameSite=Strict` con un id aleatorio.
 * - Proxy: `/bff/api/{network|routing}/<ruta>` → `/api/v1/<ruta>` con la `X-API-Key` de la sesión,
 *   solo para las rutas del contrato (docs/03-api.md) en una lista blanca. La autorización por rol
 *   la sigue decidiendo cada servicio.
 * - CSRF: los métodos que modifican exigen el encabezado `X-ServicioCerca: 1` (un formulario de
 *   otro sitio no puede enviarlo) además de la cookie `SameSite=Strict`.
 * - Errores con el formato del contrato `{code, message, details}`, sin detalles internos.
 */
import { serveStatic } from "@hono/node-server/serve-static";
import { Hono, type Context } from "hono";
import { bodyLimit } from "hono/body-limit";
import { deleteCookie, getCookie, setCookie } from "hono/cookie";
import { secureHeaders } from "hono/secure-headers";
import type { ContentfulStatusCode } from "hono/utils/http-status";

import type { Config } from "./config.js";
import type { Role, SessionStore } from "./sessions.js";

export const SESSION_COOKIE = "sc_session";
export const CSRF_HEADER = "x-serviciocerca";
export const MAX_BODY_BYTES = 2 * 1024 * 1024;

const UI_ROLES: ReadonlySet<string> = new Set<Role>(["coordinator", "operator"]);
const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"]);
const SEGMENT = "[A-Za-z0-9_-]{1,64}";

type Route = readonly [method: string, path: RegExp];

interface Upstream {
  name: string;
  baseUrl: string;
  routes: readonly Route[];
}

const NETWORK_ROUTES: readonly Route[] = [
  ["GET", /^network$/],
  ["POST", /^network\/import$/],
  ["GET", /^nodes$/],
  ["POST", /^nodes$/],
  ["GET", new RegExp(`^nodes/${SEGMENT}$`)],
  ["DELETE", new RegExp(`^nodes/${SEGMENT}$`)],
  ["GET", /^edges$/],
  ["POST", /^edges$/],
  ["DELETE", new RegExp(`^edges/${SEGMENT}$`)],
];

const ROUTING_ROUTES: readonly Route[] = [
  ["GET", /^coverage$/],
  ["GET", /^routes\/cheapest$/],
  ["GET", /^attention\/best$/],
];

export interface AppDeps {
  config: Config;
  sessions: SessionStore;
  fetch?: typeof fetch;
}

const errorBody = (code: string, message: string, details: Record<string, unknown> = {}) => ({
  code,
  message,
  details,
});

function apiError(
  c: Context,
  status: ContentfulStatusCode,
  code: string,
  message: string,
): Response {
  return c.json(errorBody(code, message), status);
}

export function createApp({ config, sessions, fetch: fetchFn = fetch }: AppDeps): Hono {
  const app = new Hono();
  const upstreams: Record<string, Upstream> = {
    network: { name: "network-service", baseUrl: config.networkServiceUrl, routes: NETWORK_ROUTES },
    routing: { name: "routing-service", baseUrl: config.routingServiceUrl, routes: ROUTING_ROUTES },
  };

  const callUpstream = (url: string, init: RequestInit = {}): Promise<Response> =>
    fetchFn(url, { ...init, signal: AbortSignal.timeout(config.requestTimeoutMs) });

  const unavailable = (c: Context, name: string): Response =>
    apiError(c, 503, "SERVICE_UNAVAILABLE", `No fue posible contactar ${name}.`);

  const relay = async (c: Context, response: Response): Promise<Response> => {
    if (response.status === 204) return c.body(null, 204);
    const text = await response.text();
    let body: unknown;
    try {
      body = JSON.parse(text);
    } catch {
      return apiError(c, 502, "BAD_GATEWAY", "Respuesta inesperada del servicio.");
    }
    return c.json(body, response.status as ContentfulStatusCode);
  };

  app.use(
    "*",
    secureHeaders({
      contentSecurityPolicy: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'"],
        // Radix y sonner fijan estilos en línea; no ejecutan código.
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["'self'", "data:"],
        fontSrc: ["'self'"],
        connectSrc: ["'self'"],
        objectSrc: ["'none'"],
        baseUri: ["'self'"],
        formAction: ["'self'"],
        frameAncestors: ["'none'"],
      },
      referrerPolicy: "no-referrer",
      crossOriginEmbedderPolicy: false,
    }),
  );

  app.use("/bff/*", async (c, next) => {
    c.header("Cache-Control", "no-store");
    if (!SAFE_METHODS.has(c.req.method) && c.req.header(CSRF_HEADER) !== "1") {
      return c.json(errorBody("FORBIDDEN", "Solicitud rechazada."), 403);
    }
    await next();
  });

  app.use(
    "/bff/*",
    bodyLimit({
      maxSize: MAX_BODY_BYTES,
      onError: (c) =>
        c.json(errorBody("PAYLOAD_TOO_LARGE", "El archivo es demasiado grande."), 413),
    }),
  );

  app.get("/healthz", (c) => c.json({ status: "ok" }));

  app.get("/bff/health", async (c) => {
    const services = await Promise.all(
      Object.values(upstreams).map(async ({ name, baseUrl }) => {
        try {
          const response = await callUpstream(`${baseUrl}/health`);
          return { name, status: response.ok ? "ok" : "down" };
        } catch {
          return { name, status: "down" };
        }
      }),
    );
    return c.json({ services });
  });

  // Sin sesión no es un error: la SPA consulta esto al cargar y muestra el inicio de sesión.
  app.get("/bff/session", (c) => {
    const session = sessions.get(getCookie(c, SESSION_COOKIE));
    return c.json({ role: session?.role ?? null });
  });

  app.post("/bff/session", async (c) => {
    let apiKey: unknown;
    try {
      apiKey = (await c.req.json<{ api_key?: unknown }>()).api_key;
    } catch {
      apiKey = undefined;
    }
    if (typeof apiKey !== "string" || apiKey.trim() === "" || apiKey.length > 256) {
      return apiError(c, 422, "VALIDATION_ERROR", "Ingrese su API key.");
    }
    let response: Response;
    try {
      response = await callUpstream(`${config.networkServiceUrl}/api/v1/auth/whoami`, {
        headers: { "X-API-Key": apiKey, Accept: "application/json" },
      });
    } catch {
      return unavailable(c, "network-service");
    }
    if (!response.ok) return relay(c, response);
    const { role } = (await response.json()) as { role?: unknown };
    if (typeof role !== "string" || !UI_ROLES.has(role)) {
      return apiError(c, 403, "FORBIDDEN", "Esta clave no corresponde a un usuario de la consola.");
    }
    sessions.delete(getCookie(c, SESSION_COOKIE)); // nunca se reutiliza un id previo
    const id = sessions.create(apiKey, role as Role);
    setCookie(c, SESSION_COOKIE, id, {
      httpOnly: true,
      sameSite: "Strict",
      secure: config.cookieSecure,
      path: "/",
      maxAge: config.sessionTtlMinutes * 60,
    });
    return c.json({ role });
  });

  app.delete("/bff/session", (c) => {
    sessions.delete(getCookie(c, SESSION_COOKIE));
    deleteCookie(c, SESSION_COOKIE, { path: "/" });
    return c.body(null, 204);
  });

  app.all("/bff/api/*", async (c) => {
    const url = new URL(c.req.url);
    const match = /^\/bff\/api\/([a-z]+)\/(.+)$/.exec(url.pathname);
    const upstream = match ? upstreams[match[1] ?? ""] : undefined;
    const path = match?.[2] ?? "";
    const method = c.req.method;
    if (!upstream || !upstream.routes.some(([m, re]) => m === method && re.test(path))) {
      return apiError(c, 404, "NOT_FOUND", "Recurso no encontrado.");
    }
    const cookie = getCookie(c, SESSION_COOKIE);
    const session = sessions.get(cookie);
    if (!session) return apiError(c, 401, "UNAUTHENTICATED", "Inicie sesión con su API key.");

    const headers: Record<string, string> = {
      "X-API-Key": session.apiKey,
      Accept: "application/json",
    };
    const init: RequestInit = { method, headers };
    if (method === "POST") {
      headers["Content-Type"] = "application/json";
      init.body = await c.req.text();
    }
    let response: Response;
    try {
      response = await callUpstream(`${upstream.baseUrl}/api/v1/${path}${url.search}`, init);
    } catch {
      return unavailable(c, upstream.name);
    }
    if (response.status === 401) sessions.delete(cookie); // la clave dejó de ser válida
    return relay(c, response);
  });

  app.all("/bff/*", (c) => apiError(c, 404, "NOT_FOUND", "Recurso no encontrado."));

  app.use("*", serveStatic({ root: config.staticDir }));
  app.get("*", serveStatic({ root: config.staticDir, path: "index.html" }));

  app.onError((error, c) => {
    console.error(error);
    return apiError(c, 500, "INTERNAL_ERROR", "Error interno de la consola.");
  });

  return app;
}
