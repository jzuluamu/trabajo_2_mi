import { api, ApiError } from "@/lib/api";
import { createQueryClient, SESSION_KEY } from "@/lib/query-client";

const json = (status: number, body: unknown) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("api", () => {
  it("envía el encabezado anti-CSRF, la cookie de sesión y JSON", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(json(200, { role: "operator" }));
    await api.login("clave");
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("/bff/session");
    expect(init).toMatchObject({
      method: "POST",
      credentials: "same-origin",
      body: '{"api_key":"clave"}',
    });
    expect((init?.headers as Record<string, string>)["X-ServicioCerca"]).toBe("1");
  });

  it("codifica ids en la ruta y arma la consulta de cobertura", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockImplementation(() => Promise.resolve(new Response(null, { status: 204 })));
    await api.deleteNode("A/B");
    await api.deleteEdge("E 1");
    await api.coverage("B_NORTE", "Z_CENTRO", true);
    await api.coverage("B_NORTE", null, false);
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual([
      "/bff/api/network/nodes/A%2FB",
      "/bff/api/network/edges/E%201",
      "/bff/api/routing/coverage?base=B_NORTE&trace=true&zone=Z_CENTRO",
      "/bff/api/routing/coverage?base=B_NORTE&trace=false",
    ]);
  });

  it("traduce errores del contrato a ApiError", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      json(404, {
        code: "ZONE_NOT_FOUND",
        message: "La zona 'Z_X' no existe.",
        details: { node_id: "Z_X" },
      }),
    );
    await expect(api.network()).rejects.toMatchObject({
      code: "ZONE_NOT_FOUND",
      message: "La zona 'Z_X' no existe.",
      status: 404,
      details: { node_id: "Z_X" },
    });
  });

  it("una respuesta sin el formato del contrato da un mensaje genérico", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response("<html>", { status: 502 }));
    await expect(api.health()).rejects.toMatchObject({
      code: "HTTP_502",
      message: "Respuesta inesperada del servicio.",
    });
    vi.spyOn(globalThis, "fetch").mockResolvedValue(json(500, ["lista"]));
    await expect(api.health()).rejects.toMatchObject({ code: "HTTP_500", details: {} });
  });

  it("un fallo de red es SERVICE_UNAVAILABLE", async () => {
    vi.spyOn(globalThis, "fetch").mockRejectedValue(new TypeError("Failed to fetch"));
    await expect(api.session()).rejects.toEqual(
      new ApiError("SERVICE_UNAVAILABLE", "No fue posible contactar la consola."),
    );
  });
});

describe("createQueryClient", () => {
  it("un 401 en cualquier consulta cierra la sesión local", async () => {
    const client = createQueryClient();
    client.setQueryData(SESSION_KEY, "operator");
    await client
      .query({
        queryKey: ["x"],
        queryFn: () => Promise.reject(new ApiError("UNAUTHENTICATED", "x", 401)),
      })
      .catch(() => undefined);
    expect(client.getQueryData(SESSION_KEY)).toBeNull();
  });

  it("reintenta una vez los fallos de red, nunca los 4xx", () => {
    const retry = createQueryClient().getDefaultOptions().queries?.retry as (
      n: number,
      e: unknown,
    ) => boolean;
    expect(retry(0, new ApiError("SERVICE_UNAVAILABLE", "x"))).toBe(true);
    expect(retry(1, new ApiError("SERVICE_UNAVAILABLE", "x"))).toBe(false);
    expect(retry(0, new ApiError("ZONE_NOT_FOUND", "x", 404))).toBe(false);
    expect(retry(0, new ApiError("X", "x", 503))).toBe(true);
    const noRetry = createQueryClient({ retry: false }).getDefaultOptions().queries?.retry as (
      n: number,
      e: unknown,
    ) => boolean;
    expect(noRetry(0, new Error("x"))).toBe(false);
  });
});
