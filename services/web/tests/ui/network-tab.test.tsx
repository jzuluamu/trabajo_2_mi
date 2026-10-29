import { act, screen, within } from "@testing-library/react";

import { FakeBff } from "./fake-bff";
import { choose, lastCy, renderWithProviders } from "./render";

beforeEach(() => {
  window.history.replaceState(null, "", "/");
});

async function openNetwork(role: "operator" | "coordinator" = "operator", empty = false) {
  const bff = new FakeBff({ role, empty }).install();
  const view = renderWithProviders();
  await screen.findByRole("heading", { name: "Red de cobertura" });
  return { ...view, bff };
}

describe("pestaña Red", () => {
  it("muestra los indicadores de la red demo", async () => {
    await openNetwork();
    const kpis = screen.getByText("Bases").closest("dl")!;
    expect(within(kpis).getByText("2 con técnico libre")).toBeInTheDocument();
    expect(within(kpis).getByText("7 con trayectos")).toBeInTheDocument();
    expect(within(kpis).getByText("1 de un solo sentido")).toBeInTheDocument();
    expect(within(kpis).getByText("ninguna base llega")).toBeInTheDocument();
  });

  it("dibuja la red completa en el mapa con un resumen accesible", async () => {
    await openNetwork();
    expect(screen.getByRole("img", { name: /3 bases, 8 zonas y 9 trayectos/ })).toBeInTheDocument();
    const cy = lastCy();
    expect(cy.nodes()).toHaveLength(11);
    expect(cy.getElementById("Z_ISLA").hasClass("isolated")).toBe(true);
    expect(cy.getElementById("E08").hasClass("oneway")).toBe(true);
  });

  it("abre con el mapa completo y la ficha del primer lugar", async () => {
    await openNetwork();
    const card = screen.getByRole("complementary", { name: "Detalle del lugar" });
    expect(within(card).getByRole("heading", { name: "Base Norte" })).toBeInTheDocument();
    expect(within(card).getByText("Ana")).toBeInTheDocument();
    expect(within(card).getByText("Disponible")).toBeInTheDocument();
    expect(within(card).getByText("No disponible")).toBeInTheDocument();
    const links = within(card).getByRole("list", { name: "Trayectos de Base Norte" });
    expect(within(links).getByText("Centro")).toBeInTheDocument();
    expect(within(links).getAllByText("ida y vuelta")).toHaveLength(2);
    expect(lastCy().elements(".faded, .selected")).toHaveLength(0);
  });

  it("elegir un lugar en la lista lo resalta en el mapa y muestra sus avisos", async () => {
    const { user } = await openNetwork();
    await choose(user, "Ver detalle de", "Base Oeste");
    expect(
      await screen.findByText(/Base sin técnicos disponibles: llega a sus zonas/),
    ).toBeInTheDocument();
    expect(lastCy().getElementById("B_OESTE").hasClass("selected")).toBe(true);
    expect(lastCy().getElementById("Z_ISLA").hasClass("faded")).toBe(true);
  });

  it("describe el sentido de los trayectos de un solo sentido", async () => {
    const { user } = await openNetwork();
    await choose(user, "Ver detalle de", "Estación");
    expect(await screen.findByText("solo llegada (desde allá)")).toBeInTheDocument();
    await choose(user, "Ver detalle de", "Delicias");
    expect(await screen.findByText("solo ida (hacia allá)")).toBeInTheDocument();
  });

  it("un clic en un nodo del mapa abre su ficha; un clic en el fondo quita el resaltado", async () => {
    await openNetwork();
    const cy = lastCy();
    act(() => {
      cy.getElementById("Z_ISLA").emit("tap");
    });
    expect(
      await screen.findByText("Sin trayectos registrados: ninguna base puede llegar a esta zona."),
    ).toBeInTheDocument();
    expect(cy.getElementById("Z_ISLA").hasClass("selected")).toBe(true);
    act(() => {
      cy.emit("tap");
    });
    expect(cy.elements(".faded")).toHaveLength(0);
    expect(screen.getByRole("heading", { name: "Isla" })).toBeInTheDocument();
  });

  it("una base sin técnicos lo indica", async () => {
    const bff = new FakeBff({ role: "operator" });
    bff.network.nodes.push({ id: "B_X", type: "BASE", name: "Base X", technicians: [] });
    bff.install();
    const { user } = renderWithProviders();
    await screen.findByRole("heading", { name: "Red de cobertura" });
    await choose(user, "Ver detalle de", "Base X");
    expect(await screen.findByText("Sin técnicos registrados.")).toBeInTheDocument();
  });

  it("ofrece la red como tabla accesible", async () => {
    const { user } = await openNetwork();
    await user.click(screen.getByRole("button", { name: "Ver como tabla (accesible)" }));
    const nodes = screen.getByRole("table", { name: "Bases y zonas" });
    expect(within(nodes).getByText("Ana (T01) ✔, Luis (T02) ✘")).toBeInTheDocument();
    const edges = screen.getByRole("table", { name: "Conexiones" });
    expect(within(edges).getByText("→ solo ida")).toBeInTheDocument();
  });

  it("Actualizar vuelve a leer la red", async () => {
    const { user, bff } = await openNetwork();
    const before = bff.requests.filter((r) => r.path === "/bff/api/network/network").length;
    await user.click(screen.getByRole("button", { name: "Actualizar" }));
    await vi.waitFor(() => {
      expect(bff.requests.filter((r) => r.path === "/bff/api/network/network").length).toBe(
        before + 1,
      );
    });
  });

  it("red vacía: explica qué hacer y lleva al coordinador a Configurar red", async () => {
    const { user } = await openNetwork("coordinator", true);
    expect(screen.getByText("La red está vacía")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ir a Configurar red" }));
    expect(await screen.findByRole("heading", { name: "Configurar red" })).toBeInTheDocument();
  });

  it("red vacía para el operador: sin acción de configurar", async () => {
    await openNetwork("operator", true);
    expect(screen.getByText("La red está vacía")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ir a Configurar red" })).not.toBeInTheDocument();
  });
});
