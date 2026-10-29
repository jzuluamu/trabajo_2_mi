/** Configuración del BFF desde variables de entorno. No guarda API keys: cada usuario ingresa la suya. */

export interface Config {
  networkServiceUrl: string;
  routingServiceUrl: string;
  port: number;
  requestTimeoutMs: number;
  sessionTtlMinutes: number;
  cookieSecure: boolean;
  staticDir: string;
}

export class ConfigError extends Error {}

function serviceUrl(env: NodeJS.ProcessEnv, name: string): string {
  const raw = env[name];
  if (!raw) throw new ConfigError(`Falta la variable ${name}.`);
  let url: URL;
  try {
    url = new URL(raw);
  } catch {
    throw new ConfigError(`${name} no es una URL válida.`);
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new ConfigError(`${name} debe usar http o https.`);
  }
  return url.origin;
}

function positiveInt(env: NodeJS.ProcessEnv, name: string, fallback: number): number {
  const raw = env[name];
  if (raw === undefined || raw === "") return fallback;
  const value = Number(raw);
  if (!Number.isInteger(value) || value <= 0) {
    throw new ConfigError(`${name} debe ser un entero positivo.`);
  }
  return value;
}

export function loadConfig(env: NodeJS.ProcessEnv = process.env): Config {
  return {
    networkServiceUrl: serviceUrl(env, "NETWORK_SERVICE_URL"),
    routingServiceUrl: serviceUrl(env, "ROUTING_SERVICE_URL"),
    port: positiveInt(env, "PORT", 8080),
    requestTimeoutMs: positiveInt(env, "REQUEST_TIMEOUT_MS", 5000),
    sessionTtlMinutes: positiveInt(env, "SESSION_TTL_MINUTES", 480),
    cookieSecure: env.COOKIE_SECURE === "true",
    staticDir: env.STATIC_DIR ?? "./dist/client",
  };
}
