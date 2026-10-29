import { act, screen } from "@testing-library/react";

import { DEMO } from "../fixtures";
import { lastCy, renderWithProviders } from "./render";
import { NetworkGraph } from "@/components/network-graph";
import { ThemeContext } from "@/hooks/use-theme";
import { DARK_PALETTE, LIGHT_PALETTE } from "@/lib/graph-elements";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("NetworkGraph", () => {
  it("el contenedor del mapa tiene tamaño propio (Cytoscape lo fuerza a position: relative)", () => {
    renderWithProviders(<NetworkGraph network={DEMO} />);
    const container = screen.getByTestId("network-graph");
    expect(container).toHaveClass("size-full");
    expect(container).not.toHaveClass("absolute");
  });

  it("conserva las posiciones de los nodos al recargar la red", () => {
    const { rerender } = renderWithProviders(<NetworkGraph network={DEMO} />);
    const first = lastCy();
    first.getElementById("B_NORTE").position({ x: 999, y: 111 });
    first.emit("dragfree");
    rerender(<NetworkGraph network={structuredClone(DEMO)} />);
    const second = lastCy();
    expect(second).not.toBe(first);
    expect(second.getElementById("B_NORTE").position()).toEqual({ x: 999, y: 111 });
  });

  it("muestra el resumen del elemento bajo el puntero", () => {
    renderWithProviders(<NetworkGraph network={DEMO} />);
    const cy = lastCy();
    act(() => {
      cy.getElementById("E08").emit({
        type: "mouseover",
        renderedPosition: { x: 40, y: 60 },
      } as never);
    });
    const tooltip = screen.getByRole("tooltip");
    expect(tooltip).toHaveTextContent("Delicias → Estación · 7 min · solo ida (E08)");
    expect(tooltip).toHaveStyle({ left: "40px", top: "60px" });
    act(() => {
      cy.emit("mouseout");
    });
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("los controles hacen zoom, ajustan y reorganizan", async () => {
    // Movimiento reducido: la reorganización es inmediata, sin animación.
    vi.stubGlobal("matchMedia", (query: string) => ({
      matches: query.includes("reduce"),
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }));
    const { user } = renderWithProviders(<NetworkGraph network={DEMO} />);
    const cy = lastCy();
    const zoom = cy.zoom();
    await user.click(screen.getByRole("button", { name: "Acercar" }));
    expect(cy.zoom()).toBeGreaterThan(zoom);
    await user.click(screen.getByRole("button", { name: "Alejar" }));
    await user.click(screen.getByRole("button", { name: "Alejar" }));
    expect(cy.zoom()).toBeLessThan(zoom);
    cy.getElementById("Z_CENTRO").position({ x: 5000, y: 5000 });
    await user.click(screen.getByRole("button", { name: "Reorganizar" }));
    expect(cy.getElementById("Z_CENTRO").position().x).toBeLessThan(5000);
    await user.click(screen.getByRole("button", { name: "Ajustar a la vista" }));
  });

  it("usa la paleta oscura con el tema oscuro y no se rompe sin nodos", () => {
    const { rerender } = renderWithProviders(<NetworkGraph network={DEMO} />);
    const light: unknown = lastCy().getElementById("B_NORTE").style("background-color");
    rerender(
      <ThemeContext
        value={{ preference: "dark", resolved: "dark", setPreference: () => undefined }}
      >
        <NetworkGraph network={DEMO} />
      </ThemeContext>,
    );
    const dark: unknown = lastCy().getElementById("B_NORTE").style("background-color");
    expect(light).not.toBe(dark);
    expect(LIGHT_PALETTE.base).not.toBe(DARK_PALETTE.base);
    rerender(<NetworkGraph network={{ nodes: [], edges: [] }} />);
    expect(screen.getByText("Aún no hay nodos para dibujar.")).toBeInTheDocument();
  });
});
