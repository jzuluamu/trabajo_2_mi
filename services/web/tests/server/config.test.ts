import { ConfigError, loadConfig } from "../../server/config.js";

const base = {
  NETWORK_SERVICE_URL: "http://network:8001/",
  ROUTING_SERVICE_URL: "http://routing:8002",
};

describe("loadConfig", () => {
  it("usa valores por omisión seguros", () => {
    expect(loadConfig(base)).toEqual({
      networkServiceUrl: "http://network:8001",
      routingServiceUrl: "http://routing:8002",
      port: 8080,
      requestTimeoutMs: 5000,
      sessionTtlMinutes: 480,
      cookieSecure: false,
      staticDir: "./dist/client",
    });
  });

  it("lee los valores opcionales", () => {
    const config = loadConfig({
      ...base,
      PORT: "9000",
      REQUEST_TIMEOUT_MS: "100",
      SESSION_TTL_MINUTES: "5",
      COOKIE_SECURE: "true",
      STATIC_DIR: "/srv",
    });
    expect(config).toMatchObject({
      port: 9000,
      requestTimeoutMs: 100,
      sessionTtlMinutes: 5,
      cookieSecure: true,
      staticDir: "/srv",
    });
  });

  it.each([
    [{ ROUTING_SERVICE_URL: "http://r" }, "Falta la variable NETWORK_SERVICE_URL."],
    [{ ...base, NETWORK_SERVICE_URL: "no-es-url" }, "NETWORK_SERVICE_URL no es una URL válida."],
    [
      { ...base, ROUTING_SERVICE_URL: "file:///etc/passwd" },
      "ROUTING_SERVICE_URL debe usar http o https.",
    ],
    [{ ...base, PORT: "-1" }, "PORT debe ser un entero positivo."],
    [{ ...base, SESSION_TTL_MINUTES: "1.5" }, "SESSION_TTL_MINUTES debe ser un entero positivo."],
  ])("falla al arrancar con configuración inválida", (env, message) => {
    expect(() => loadConfig(env)).toThrow(new ConfigError(message));
  });
});
