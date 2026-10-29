/**
 * Sesiones en memoria del BFF: la API key vive solo aquí, nunca en el navegador.
 * El navegador recibe un id aleatorio de 256 bits en una cookie HttpOnly (ver app.ts).
 * Caducidad deslizante: cada uso renueva el plazo. Un reinicio del servidor cierra todas las sesiones.
 */
import { randomBytes } from "node:crypto";

export type Role = "coordinator" | "operator";

export interface Session {
  apiKey: string;
  role: Role;
  expiresAt: number;
}

export class SessionStore {
  private readonly sessions = new Map<string, Session>();

  constructor(
    private readonly ttlMs: number,
    private readonly maxSessions = 1000,
    private readonly now: () => number = Date.now,
  ) {}

  get size(): number {
    return this.sessions.size;
  }

  create(apiKey: string, role: Role): string {
    this.sweep();
    if (this.sessions.size >= this.maxSessions) {
      const oldest = this.sessions.keys().next().value;
      if (oldest !== undefined) this.sessions.delete(oldest);
    }
    const id = randomBytes(32).toString("base64url");
    this.sessions.set(id, { apiKey, role, expiresAt: this.now() + this.ttlMs });
    return id;
  }

  get(id: string | undefined): Session | undefined {
    if (id === undefined) return undefined;
    const session = this.sessions.get(id);
    if (session === undefined) return undefined;
    if (session.expiresAt <= this.now()) {
      this.sessions.delete(id);
      return undefined;
    }
    session.expiresAt = this.now() + this.ttlMs;
    return session;
  }

  delete(id: string | undefined): void {
    if (id !== undefined) this.sessions.delete(id);
  }

  private sweep(): void {
    const now = this.now();
    for (const [id, session] of this.sessions) {
      if (session.expiresAt <= now) this.sessions.delete(id);
    }
  }
}
