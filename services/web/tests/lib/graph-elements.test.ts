import { coverageOverlay } from "@/lib/coverage-format";
import {
  buildElements,
  draftElement,
  graphStyle,
  graphSummary,
  idealEdgeLength,
  LIGHT_PALETTE,
  overlayFor,
} from "@/lib/graph-elements";

import { COVERAGE_NORTE, DEMO } from "../fixtures";

describe("buildElements", () => {
  const elements = buildElements(DEMO);
  const byId = (id: string) => elements.find((element) => element.data.id === id)!;

  it("codifica tipo y estado en clases y en el texto de la etiqueta", () => {
    expect(byId("B_NORTE").classes).toEqual(["base", "free"]);
    expect(byId("B_NORTE").data.label).toBe("Base Norte\n1 técnico libre");
    expect(byId("B_OESTE").classes).toEqual(["base", "idle"]);
    expect(byId("B_OESTE").data.label).toBe("Base Oeste\nsin técnicos libres");
    expect(byId("Z_ISLA").classes).toEqual(["zone", "isolated"]);
    expect(byId("Z_ISLA").data.tooltip).toContain("ninguna base llega");
    expect(byId("Z_CENTRO").data.tooltip).toBe("Centro (Z_CENTRO) · zona · 3 trayectos");
    expect(byId("E08").classes).toEqual(["oneway"]);
    expect(byId("E01").data.tooltip).toBe("Base Norte ↔ Centro · 30 min · ambos sentidos (E01)");
  });

  it("posiciones iniciales deterministas", () => {
    expect(buildElements(DEMO).map((e) => e.position)).toEqual(elements.map((e) => e.position));
  });

  it("varios técnicos libres en plural", () => {
    const network = {
      nodes: [
        {
          id: "B",
          type: "BASE" as const,
          name: "B",
          technicians: [
            { id: "1", name: "a", available: true },
            { id: "2", name: "b", available: true },
          ],
        },
      ],
      edges: [{ id: "E", source: "B", target: "X", weight: 3, bidirectional: true }],
    };
    expect(buildElements(network)[0]?.data.label).toBe("B\n2 técnicos libres");
    expect(buildElements(network)[1]?.data.tooltip).toBe("B ↔ X · 3 min · ambos sentidos (E)");
  });

  it("la longitud de la arista crece con los minutos, con tope", () => {
    expect(idealEdgeLength(5)).toBeLessThan(idealEdgeLength(30));
    expect(idealEdgeLength(60)).toBe(idealEdgeLength(500));
  });
});

describe("draftElement", () => {
  it("dibuja la conexión válida o marca 'revisar'", () => {
    const valid = draftElement(DEMO, {
      source: "B_NORTE",
      target: "Z_ISLA",
      weight: 12,
      bidirectional: true,
      valid: true,
    });
    expect(valid?.data.label).toBe("12 min · vista previa");
    expect(valid?.classes).toEqual(["draft"]);
    const invalid = draftElement(DEMO, {
      source: "B_NORTE",
      target: "Z_ISLA",
      weight: -5,
      bidirectional: false,
      valid: false,
    });
    expect(invalid?.data.label).toBe("revisar");
    expect(invalid?.classes).toEqual(["draft", "invalid", "oneway"]);
    expect(invalid?.data.weight).toBe(1);
  });

  it("no dibuja nada sin datos completos", () => {
    expect(draftElement(DEMO, null)).toBeNull();
    expect(
      draftElement(DEMO, {
        source: "B_NORTE",
        target: "B_NORTE",
        weight: 1,
        bidirectional: true,
        valid: true,
      }),
    ).toBeNull();
    expect(
      draftElement(DEMO, {
        source: "B_NORTE",
        target: "NADA",
        weight: 1,
        bidirectional: true,
        valid: true,
      }),
    ).toBeNull();
  });
});

describe("overlayFor", () => {
  it("selección: el nodo, sus trayectos y vecinos; el resto atenuado", () => {
    const { classes } = overlayFor(DEMO, { selected: "Z_CENTRO" });
    expect(classes.get("Z_CENTRO")).toEqual(["selected"]);
    expect(classes.get("E01")).toEqual(["neighbor"]);
    expect(classes.has("B_NORTE")).toBe(false);
    expect(classes.get("Z_ISLA")).toEqual(["faded"]);
    expect(classes.get("E09")).toEqual(["faded"]);
  });

  it("sin selección válida no cambia nada", () => {
    expect(overlayFor(DEMO, { selected: "NADA" }).classes.size).toBe(0);
    expect(overlayFor(DEMO, {}).classes.size).toBe(0);
  });

  it("cobertura: origen, tramos, sin cobertura y fuera del alcance", () => {
    const { classes, labels } = overlayFor(DEMO, {
      coverage: coverageOverlay(COVERAGE_NORTE),
      selected: "Z_CENTRO",
    });
    expect(classes.get("B_NORTE")).toEqual(["origin"]);
    expect(labels.get("B_NORTE")).toBe("Base Norte\norigen");
    expect(classes.get("Z_BOSQUE")).toEqual(["reached", "hop-2"]);
    expect(labels.get("Z_BOSQUE")).toBe("Bosque\n2 tramos");
    expect(classes.get("Z_ESTACION")).toEqual(["reached", "hop-4"]);
    expect(classes.get("Z_ISLA")).toEqual(["unreached"]);
    expect(classes.get("B_OESTE")).toEqual(["faded"]);
    expect(classes.get("E08")).toEqual(["reached"]);
    expect(classes.get("E09")).toEqual(["faded"]);
    expect(classes.get("Z_CENTRO")).toEqual(["reached", "hop-1", "selected"]);
  });

  it("ignora una cobertura de una base que ya no existe", () => {
    const overlay = overlayFor(DEMO, {
      coverage: coverageOverlay({ ...COVERAGE_NORTE, base: "B_BORRADA" }),
    });
    expect(overlay.classes.size).toBe(0);
  });
});

describe("estilo y resumen", () => {
  it("usa los colores del sistema visual", () => {
    const style = graphStyle(LIGHT_PALETTE);
    const base = style.find((block) => "selector" in block && block.selector === "node.base");
    expect(base && "style" in base ? base.style : null).toMatchObject({
      "background-color": "#262626",
    });
  });

  it("resume la red en singular y plural", () => {
    expect(graphSummary(DEMO)).toContain("3 bases, 8 zonas y 9 trayectos");
    expect(
      graphSummary({ nodes: [{ id: "B", type: "BASE", name: "B", technicians: [] }], edges: [] }),
    ).toContain("1 base, 0 zonas y 0 trayectos");
  });
});
