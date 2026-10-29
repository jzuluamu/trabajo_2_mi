import {
  coverageOverlay,
  coverageSummary,
  reachableRows,
  traceRows,
  unreachableRows,
} from "@/lib/coverage-format";

import { COVERAGE_NORTE, DEMO } from "../fixtures";

describe("coverage-format", () => {
  it("filas legibles con nombre y tipo", () => {
    expect(reachableRows(DEMO, COVERAGE_NORTE)[0]).toEqual({
      id: "Z_ALAMEDA",
      name: "Alameda",
      type: "Zona",
      hops: 1,
    });
    expect(unreachableRows(DEMO, COVERAGE_NORTE)).toEqual([
      { id: "Z_FUENTE", name: "Fuente" },
      { id: "Z_ISLA", name: "Isla" },
    ]);
    expect(unreachableRows({ nodes: [], edges: [] }, COVERAGE_NORTE)[0]?.name).toBe("Z_FUENTE");
    expect(reachableRows({ nodes: [], edges: [] }, COVERAGE_NORTE)[0]?.name).toBe("Z_ALAMEDA");
  });

  it("traduce la traza y tolera datos ausentes", () => {
    const report = {
      ...COVERAGE_NORTE,
      trace: [
        { step: 1, action: "visit", node: "B_NORTE", data: { hops: 0 } },
        { step: 2, action: "enqueue", node: "Z_ALAMEDA", data: { hops: 1, from: "B_NORTE" } },
        { step: 3, action: "otra", node: "X", data: {} },
      ],
    };
    expect(traceRows(report)).toEqual([
      { step: 1, action: "Visita", node: "B_NORTE", hops: "0", from: "" },
      { step: 2, action: "Encola", node: "Z_ALAMEDA", hops: "1", from: "B_NORTE" },
      { step: 3, action: "otra", node: "X", hops: "", from: "" },
    ]);
    expect(traceRows(COVERAGE_NORTE)).toEqual([]);
  });

  it("mapa de tramos para el grafo", () => {
    const overlay = coverageOverlay(COVERAGE_NORTE);
    expect(overlay.origin).toBe("B_NORTE");
    expect(overlay.hops.get("Z_ESTACION")).toBe(4);
    expect(overlay.unreachable.has("Z_ISLA")).toBe(true);
  });

  it("resume la cobertura en una frase sin términos técnicos", () => {
    expect(coverageSummary(DEMO, COVERAGE_NORTE)).toBe(
      "Base Norte llega a 6 zonas y 1 base. Quedan sin cobertura Fuente e Isla.",
    );
    const one = {
      ...COVERAGE_NORTE,
      reachable: [COVERAGE_NORTE.reachable[0]!],
      unreachable_zones: ["Z_ISLA"],
    };
    expect(coverageSummary(DEMO, one)).toBe("Base Norte llega a 1 zona. Queda sin cobertura Isla.");
    const none = { ...COVERAGE_NORTE, base: "B_X", reachable: [], unreachable_zones: [] };
    expect(coverageSummary(DEMO, none)).toBe(
      "B_X no llega a ningún otro lugar. Todas las zonas tienen cobertura.",
    );
    const bases = {
      ...COVERAGE_NORTE,
      reachable: [{ node_id: "B_SUR", type: "BASE" as const, hops: 1 }],
    };
    expect(coverageSummary(DEMO, bases)).toContain("llega a 1 base.");
  });
});
