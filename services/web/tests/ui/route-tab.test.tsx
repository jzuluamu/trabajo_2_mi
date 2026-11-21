import { screen, within } from "@testing-library/react";

import { FakeBff } from "./fake-bff";
import { choose, lastCy, renderWithProviders } from "./render";

beforeEach(() => {
  window.history.replaceState(null, "", "/#ruta");
});

async function openRoutes({ empty = false, role = "operator" as const } = {}) {
  const bff = new FakeBff({ role, empty }).install();
  const view = renderWithProviders();
  await screen.findByRole("heading", { name: "¿Cuál es la ruta más rápida?" });
  return { ...view, bff };
}

describe("pestaña Menor costo", () => {
  it("de A a B pinta en el mapa la ruta más rápida, con paradas y minutos", async () => {
    const { user, bff } = await openRoutes();
    expect(screen.getByRole("tab", { name: /Menor costo/ })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await choose(user, "Desde", "Base Norte");
    await choose(user, "Hasta", "Centro");
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));

    expect(
      await screen.findByText("De Base Norte a Centro: 15 min en 3 tramos, por Alameda y Bosque."),
    ).toBeInTheDocument();
    expect(bff.last("GET", "/bff/api/routing/routes/cheapest")?.path).toBe(
      "/bff/api/routing/routes/cheapest?origin=B_NORTE&destination=Z_CENTRO&trace=false",
    );
    expect(screen.getByText("Menos tramos no siempre es más rápido")).toBeInTheDocument();
    expect(
      screen.getByText(
        "El camino de menos tramos (Base Norte → Centro, 1 tramo) tarda 30 min: esta ruta ahorra 15 min.",
      ),
    ).toBeInTheDocument();

    const steps = screen.getByRole("list", { name: "Recorrido (3 tramos)" });
    const items = within(steps).getAllByRole("listitem");
    expect(items).toHaveLength(3);
    expect(items[0]).toHaveTextContent("Base Norte → Alameda");
    expect(items[2]).toHaveTextContent("Bosque → Centro");
    expect(items[2]).toHaveTextContent("15 min");

    const cy = lastCy();
    expect(cy.getElementById("B_NORTE").hasClass("route-origin")).toBe(true);
    expect(cy.getElementById("B_NORTE").data("label")).toBe("Base Norte\nsalida");
    expect(cy.getElementById("Z_ALAMEDA").data("label")).toBe("Alameda\na 5 min");
    expect(cy.getElementById("Z_BOSQUE").data("label")).toBe("Bosque\na 10 min");
    expect(cy.getElementById("Z_CENTRO").hasClass("route-destination")).toBe(true);
    expect(cy.getElementById("Z_CENTRO").data("label")).toBe("Centro\nllegada · 15 min");
    for (const id of ["E02", "E03", "E04"])
      expect(cy.getElementById(id).hasClass("route")).toBe(true);
    expect(cy.getElementById("E01").hasClass("route-alt")).toBe(true);
    expect(cy.getElementById("E05").hasClass("faded")).toBe(true);
    expect(cy.getElementById("B_SUR").hasClass("faded")).toBe(true);
    expect(
      screen.getByRole("img", { name: /Mapa de la ruta. De Base Norte a Centro/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Leyenda del mapa" })).toHaveTextContent(
      "Camino de menos tramos",
    );
  });

  it("sin camino responde en ámbar, sin error, y el mapa queda sin ruta", async () => {
    const { user } = await openRoutes();
    await choose(user, "Desde", "Base Norte");
    await choose(user, "Hasta", "Fuente");
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));

    expect(await screen.findByText("No hay ruta en ese sentido")).toBeInTheDocument();
    expect(
      screen.getAllByText(/No hay ruta de Base Norte a Fuente: ningún camino/).length,
    ).toBeGreaterThan(0);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(lastCy().getElementById("B_NORTE").hasClass("route-origin")).toBe(false);
  });

  it("invertir el sentido intercambia Desde y Hasta", async () => {
    const { user, bff } = await openRoutes();
    await choose(user, "Desde", "Centro");
    await choose(user, "Hasta", "Base Norte");
    await user.click(screen.getByRole("button", { name: "Invertir el sentido" }));
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    await screen.findByText(/De Base Norte a Centro/);
    expect(bff.last("GET", "/bff/api/routing/routes/cheapest")?.path).toContain(
      "origin=B_NORTE&destination=Z_CENTRO",
    );
  });

  it("el mismo lugar como salida y llegada cuesta 0 min", async () => {
    const { user } = await openRoutes();
    await choose(user, "Desde", "Base Norte");
    await choose(user, "Hasta", "Base Norte");
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    expect(
      await screen.findByText("Base Norte es el punto de partida y el de llegada: 0 min."),
    ).toBeInTheDocument();
    const node = lastCy().getElementById("B_NORTE");
    expect(node.hasClass("route-origin") && node.hasClass("route-destination")).toBe(true);
  });

  it("muestra el cálculo de Dijkstra paso a paso cuando se pide", async () => {
    const { user, bff } = await openRoutes();
    await choose(user, "Desde", "Base Norte");
    await choose(user, "Hasta", "Centro");
    await user.click(screen.getByRole("checkbox", { name: "Incluir el cálculo paso a paso" }));
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    await user.click(await screen.findByRole("button", { name: /Ver el cálculo paso a paso/ }));
    const table = screen.getByRole("table", { name: "Cálculo paso a paso" });
    expect(within(table).getByText("Se fija (ya es el más rápido)")).toBeInTheDocument();
    expect(within(table).getByText("Mejora el tiempo")).toBeInTheDocument();
    expect(bff.last("GET", "/bff/api/routing/routes/cheapest")?.path).toContain("trace=true");
  });

  it("un error del contrato se muestra legible", async () => {
    const { user, bff } = await openRoutes();
    bff.failures.set("GET /api/routing/routes/cheapest", {
      status: 503,
      code: "NETWORK_UNAVAILABLE",
      message: "No se pudo obtener la red de cobertura. Intente de nuevo más tarde.",
    });
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "No se pudo obtener la red de cobertura.",
    );
  });

  it("mejor base: recomienda una base con técnico y pinta su ruta", async () => {
    const { user, bff } = await openRoutes();
    await user.click(screen.getByRole("tab", { name: "Mejor base" }));
    await choose(user, "Zona a atender", "Colina");
    await user.click(screen.getByRole("checkbox", { name: "Incluir el cálculo paso a paso" }));
    await user.click(screen.getByRole("button", { name: "Buscar base" }));

    expect(
      await screen.findByText("Enviar desde Base Sur (Marta): 20 min en 2 tramos."),
    ).toBeInTheDocument();
    expect(bff.last("GET", "/bff/api/routing/attention/best")?.path).toBe(
      "/bff/api/routing/attention/best?zone=Z_COLINA&trace=true",
    );
    expect(screen.getByText("Otras bases con técnico disponible (1)")).toBeInTheDocument();
    expect(screen.getByText("Base Norte")).toBeInTheDocument();
    const cy = lastCy();
    expect(cy.getElementById("B_SUR").hasClass("route-origin")).toBe(true);
    expect(cy.getElementById("Z_COLINA").data("label")).toBe("Colina\nllegada · 20 min");
    expect(cy.getElementById("E06").hasClass("route")).toBe(true);
    expect(cy.getElementById("E07").hasClass("route")).toBe(true);
    expect(screen.getByRole("list", { name: "Leyenda del mapa" })).not.toHaveTextContent(
      "Camino de menos tramos",
    );
    await user.click(screen.getByRole("button", { name: /Ver el cálculo paso a paso/ }));
    expect(screen.getByRole("columnheader", { name: "Desde la base" })).toBeInTheDocument();
  });

  it("mejor base: explica con nombres por qué una zona no se puede atender", async () => {
    const { user } = await openRoutes();
    await user.click(screen.getByRole("tab", { name: "Mejor base" }));
    await choose(user, "Zona a atender", "Fuente");
    await user.click(screen.getByRole("button", { name: "Buscar base" }));
    expect(await screen.findByText("No se puede atender esta zona")).toBeInTheDocument();
    expect(
      screen.getAllByText(
        "Fuente no se puede atender: solo es alcanzable desde bases sin técnicos disponibles (Base Oeste).",
      ).length,
    ).toBeGreaterThan(0);
  });

  it("con la red vacía invita a cargar lugares", async () => {
    await openRoutes({ empty: true });
    expect(screen.getByText("Faltan lugares para trazar una ruta")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ver ruta" })).not.toBeInTheDocument();
  });
});

describe("pestaña Menor costo · avisos visibles", () => {
  it("el aviso de 'no hay ruta' y la comparación aparecen arriba del mapa", async () => {
    const { user } = await openRoutes();
    await choose(user, "Desde", "Base Norte");
    await choose(user, "Hasta", "Fuente");
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    const noRoute = await screen.findByText("No hay ruta en ese sentido");
    const before = (el: Element) =>
      el.compareDocumentPosition(screen.getByTestId("network-graph")) &
      Node.DOCUMENT_POSITION_FOLLOWING;
    expect(before(noRoute)).toBeTruthy();

    await choose(user, "Hasta", "Centro");
    await user.click(screen.getByRole("button", { name: "Ver ruta" }));
    expect(before(await screen.findByText("Menos tramos no siempre es más rápido"))).toBeTruthy();
  });

  it("el aviso de zona no atendible aparece arriba del mapa", async () => {
    const { user } = await openRoutes();
    await user.click(screen.getByRole("tab", { name: "Mejor base" }));
    await choose(user, "Zona a atender", "Fuente");
    await user.click(screen.getByRole("button", { name: "Buscar base" }));
    const notice = await screen.findByText("No se puede atender esta zona");
    expect(
      notice.compareDocumentPosition(screen.getByTestId("network-graph")) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});
