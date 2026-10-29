import { SessionStore } from "../../server/sessions.js";

describe("SessionStore", () => {
  it("crea ids aleatorios y largos", () => {
    const store = new SessionStore(1000);
    const a = store.create("k1", "operator");
    const b = store.create("k2", "operator");
    expect(a).not.toBe(b);
    expect(a.length).toBeGreaterThanOrEqual(43);
  });

  it("caduca tras el plazo y renueva el plazo con cada uso", () => {
    let now = 0;
    const store = new SessionStore(100, 10, () => now);
    const id = store.create("k", "coordinator");
    now = 90;
    expect(store.get(id)?.apiKey).toBe("k");
    now = 180;
    expect(store.get(id)?.role).toBe("coordinator");
    now = 300;
    expect(store.get(id)).toBeUndefined();
    expect(store.size).toBe(0);
  });

  it("ignora ids ausentes o desconocidos", () => {
    const store = new SessionStore(100);
    expect(store.get(undefined)).toBeUndefined();
    expect(store.get("otro")).toBeUndefined();
    store.delete(undefined);
    store.delete("otro");
    expect(store.size).toBe(0);
  });

  it("limpia las caducadas y respeta el máximo expulsando la más antigua", () => {
    let now = 0;
    const store = new SessionStore(100, 2, () => now);
    const first = store.create("a", "operator");
    store.create("b", "operator");
    store.create("c", "operator");
    expect(store.size).toBe(2);
    expect(store.get(first)).toBeUndefined();
    now = 500;
    store.create("d", "operator");
    expect(store.size).toBe(1);
  });
});
