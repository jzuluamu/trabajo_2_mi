import { screen, within } from "@testing-library/react";

import { FakeBff } from "./fake-bff";
import { choose, lastCy, renderWithProviders } from "./render";

beforeEach(() => {
  window.history.replaceState(null, "", "/#cobertura");
});

async function openCoverage(empty = false) {
  const bff = new FakeBff({ role: "operator", empty }).install();
  const view = renderWithProviders();
  await screen.findByRole("heading", { name: "¿Hasta dónde llega una base?" });
  return { ...view, bff };
}

describe("pestaña Cobertura", () => {
  it("resume en una frase lo que alcanza la base y lo resalta en el mapa", async () => {
    const { user, bff } = await openCoverage();
    expect(screen.getByText(/el mapa pinta de azul lo que la base alcanza/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(
      await screen.findByText(
        "Base Norte llega a 6 zonas y 1 base. Quedan sin cobertura Fuente e Isla.",
      ),
    ).toBeInTheDocument();
    const oneHop = screen.getByRole("list", { name: "A 1 tramos" });
    expect(within(oneHop).getByText("Alameda")).toBeInTheDocument();
    expect(within(oneHop).getByText("Centro")).toBeInTheDocument();
    expect(
      within(screen.getByRole("list", { name: "A 4 tramos" })).getByText("(base)"),
    ).toBeInTheDocument();
    expect(screen.getByText("Zonas sin cobertura (2)")).toBeInTheDocument();
    expect(bff.last("GET", "/bff/api/routing/coverage")?.path).toBe(
      "/bff/api/routing/coverage?base=B_NORTE&trace=false",
    );
    const cy = lastCy();
    expect(cy.getElementById("B_NORTE").hasClass("origin")).toBe(true);
    expect(cy.getElementById("Z_CENTRO").hasClass("hop-1")).toBe(true);
    expect(cy.getElementById("Z_CENTRO").data("label")).toBe("Centro\n1 tramo");
    expect(cy.getElementById("Z_FUENTE").data("label")).toBe("Fuente\nsin cobertura");
    expect(cy.getElementById("B_OESTE").hasClass("faded")).toBe(true);
    expect(
      screen.getByRole("img", { name: /Mapa de cobertura. Base Norte llega/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("list", { name: "Leyenda del mapa" })).toHaveTextContent(
      "Sin cobertura",
    );
  });

  it("una zona cubierta se informa en verde y una sin camino en ámbar, sin ser error", async () => {
    const { user } = await openCoverage();
    await choose(user, "¿Revisar una zona en particular?", "Centro");
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(await screen.findByText("Centro está cubierta")).toBeInTheDocument();
    expect(screen.getByText("Se llega desde Base Norte en 1 tramo.")).toBeInTheDocument();
    await choose(user, "¿Revisar una zona en particular?", "Fuente");
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(await screen.findByText("Fuente no está cubierta")).toBeInTheDocument();
    expect(
      screen.getByText("No hay ningún camino desde Base Norte hasta Fuente."),
    ).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("dice los tramos en plural cuando corresponde", async () => {
    const { user } = await openCoverage();
    await choose(user, "¿Revisar una zona en particular?", "Bosque");
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(await screen.findByText("Se llega desde Base Norte en 2 tramos.")).toBeInTheDocument();
  });

  it("muestra el recorrido paso a paso con nombres", async () => {
    const { user, bff } = await openCoverage();
    await user.click(screen.getByRole("checkbox", { name: "Incluir el recorrido paso a paso" }));
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    await user.click(
      await screen.findByRole("button", { name: /Ver el recorrido paso a paso \(2 pasos\)/ }),
    );
    const trace = screen.getByRole("table", { name: "Recorrido paso a paso" });
    expect(within(trace).getByText("Se agrega a la fila")).toBeInTheDocument();
    expect(within(trace).getByText("Se visita")).toBeInTheDocument();
    expect(within(trace).getAllByText("Base Norte").length).toBeGreaterThan(0);
    expect(bff.last("GET", "/bff/api/routing/coverage")?.path).toContain("trace=true");
  });

  it("explica cómo se calcula", async () => {
    const { user } = await openCoverage();
    await user.click(screen.getByRole("button", { name: "¿Cómo se calcula?" }));
    expect(screen.getByText(/recorrido en anchura \(BFS\)/)).toBeInTheDocument();
  });

  it("un error del contrato se muestra legible", async () => {
    const { user } = await openCoverage();
    await choose(user, "Base de partida", "Base Sur");
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("La base 'B_SUR' no existe.");
  });

  it("informa una base sin trayectos", async () => {
    const { user } = await openCoverage();
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          base: "B_NORTE",
          reachable: [],
          unreachable_zones: [],
          zone: null,
          trace: null,
        }),
        { status: 200 },
      ),
    );
    await user.click(screen.getByRole("button", { name: "Ver cobertura" }));
    expect(
      await screen.findByText("Esta base no tiene trayectos hacia ninguna zona."),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        "Base Norte no llega a ningún otro lugar. Todas las zonas tienen cobertura.",
      ),
    ).toBeInTheDocument();
  });

  it("sin bases explica cómo continuar", async () => {
    await openCoverage(true);
    expect(screen.getByText("Todavía no hay bases")).toBeInTheDocument();
  });
});
