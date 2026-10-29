/** Punto de entrada del BFF: solo compone y arranca (mantener sin lógica). */
import { serve } from "@hono/node-server";

import { createApp } from "./app.js";
import { loadConfig } from "./config.js";
import { SessionStore } from "./sessions.js";

const config = loadConfig();
const app = createApp({ config, sessions: new SessionStore(config.sessionTtlMinutes * 60_000) });
const server = serve({ fetch: app.fetch, port: config.port, hostname: "0.0.0.0" }, (info) => {
  console.log(`Consola web en http://0.0.0.0:${info.port}`);
});
process.on("SIGTERM", () => server.close());
