import { ApiError } from "@/lib/api";
import {
  describeError,
  edgePayload,
  errorText,
  formatMinutes,
  FormInputError,
  joinList,
  networkKpis,
  nextId,
  nodeCard,
  nodeOptions,
  nodePayload,
  parseNetworkFile,
  suggestNodeId,
  technicianSummary,
  weightInRange,
} from "@/lib/network-format";

import { DEMO } from "../fixtures";

describe("identificadores sugeridos", () => {
  it("arma el id desde el nombre, sin tildes ni la palabra del tipo", () => {
    expect(suggestNodeId("BASE", "Base Este", [])).toBe("B_ESTE");
    expect(suggestNodeId("ZONE", "Estación Sur", [])).toBe("Z_ESTACION_SUR");
    expect(suggestNodeId("ZONE", "Zona  las-palmas!", [])).toBe("Z_LAS_PALMAS");
    expect(suggestNodeId("BASE", "   ", [])).toBe("");
  });

  it("evita ids ocupados y respeta el largo máximo", () => {
    expect(suggestNodeId("BASE", "Norte", ["B_NORTE"])).toBe("B_NORTE_2");
    expect(suggestNodeId("BASE", "Norte", ["B_NORTE", "B_NORTE_2"])).toBe("B_NORTE_3");
    const long = suggestNodeId("ZONE", "a".repeat(60), ["Z_" + "A".repeat(30)]);
    expect(long.length).toBeLessThanOrEqual(32);
    expect(long.endsWith("_2")).toBe(true);
  });

  it("propone el siguiente id libre", () => {
    expect(nextId("E", ["E01", "E09", "X99", "E3"])).toBe("E10");
    expect(nextId("T", [])).toBe("T01");
  });
});

describe("nodePayload", () => {
  it("una base recibe técnicos con ids libres e ignora filas vacías", () => {
    expect(
      nodePayload(
        " B_ESTE ",
        "BASE",
        " Base Este ",
        [
          { name: "Sara", available: true },
          { name: "  ", available: true },
          { name: " Juan ", available: false },
        ],
        ["T01", "T02"],
      ),
    ).toEqual({
      id: "B_ESTE",
      type: "BASE",
      name: "Base Este",
      technicians: [
        { id: "T03", name: "Sara", available: true },
        { id: "T04", name: "Juan", available: false },
      ],
    });
  });

  it("una zona no lleva técnicos", () => {
    expect(nodePayload("Z", "ZONE", "Z", [{ name: "x", available: true }], [])).toEqual({
      id: "Z",
      type: "ZONE",
      name: "Z",
    });
  });

  it("pide nombre e identificador", () => {
    expect(() => nodePayload("Z", "ZONE", " ", [], [])).toThrow(
      new FormInputError("Escriba el nombre."),
    );
    expect(() => nodePayload(" ", "ZONE", "Z", [], [])).toThrow("Escriba un identificador.");
  });

  it("arma la conexión con el id sin espacios", () => {
    expect(edgePayload(" E1 ", "A", "B", 5, false)).toEqual({
      id: "E1",
      source: "A",
      target: "B",
      weight: 5,
      bidirectional: false,
    });
  });
});

describe("parseNetworkFile", () => {
  it("lee nodes y edges y agrega replace", () => {
    expect(parseNetworkFile('{"nodes": [1], "edges": []}', true)).toEqual({
      nodes: [1],
      edges: [],
      replace: true,
    });
  });

  it.each([
    ["{no", "El archivo no es un JSON válido."],
    ['{"nodes": []}', "El archivo debe tener las listas 'nodes' y 'edges'."],
    ["[]", "El archivo debe tener las listas 'nodes' y 'edges'."],
    ["null", "El archivo debe tener las listas 'nodes' y 'edges'."],
  ])("rechaza %j", (content, message) => {
    expect(() => parseNetworkFile(content, false)).toThrow(message);
  });
});

describe("errores", () => {
  it("agrega los campos de un VALIDATION_ERROR", () => {
    const error = new ApiError("VALIDATION_ERROR", "Datos inválidos.", 422, {
      errors: [{ field: "body.weight" }, { field: "id" }, "otro"],
    });
    expect(errorText(error)).toBe("Datos inválidos. Campos: weight, id.");
  });

  it("indica la posición en el archivo importado", () => {
    expect(errorText(new ApiError("X", "Mal.", 422, { section: "edges", index: 2 }))).toBe(
      "Mal. (archivo: conexión #3)",
    );
    expect(errorText(new ApiError("X", "Mal.", 422, { section: "nodes", index: 0 }))).toBe(
      "Mal. (archivo: nodo #1)",
    );
  });

  it("describe cualquier error", () => {
    expect(describeError(new ApiError("X", "Del contrato."))).toBe("Del contrato.");
    expect(describeError(new Error("Genérico."))).toBe("Genérico.");
    expect(describeError("raro")).toBe("Ocurrió un error inesperado.");
  });
});

describe("indicadores, ficha y opciones", () => {
  it("resume la red demo", () => {
    expect(networkKpis(DEMO).map((kpi) => [kpi.value, kpi.help])).toEqual([
      [3, "2 con técnico libre"],
      [8, "7 con trayectos"],
      [9, "1 de un solo sentido"],
      [1, "ninguna base llega"],
    ]);
    expect(networkKpis({ nodes: [], edges: [] })[3]?.help).toBe("todas conectadas");
  });

  it("ficha con flechas según el sentido y avisos", () => {
    const delicias = nodeCard(DEMO, "Z_DELICIAS")!;
    expect(delicias).toMatchObject({ name: "Delicias", typeLabel: "Zona", isBase: false });
    expect(delicias.links.map((l) => `${l.arrow} ${l.other}`)).toEqual([
      "↔ Base Sur",
      "↔ Colina",
      "→ Estación",
    ]);
    expect(nodeCard(DEMO, "Z_ESTACION")!.links[0]?.arrow).toBe("←");
    expect(nodeCard(DEMO, "B_OESTE")!.note).toContain("Base sin técnicos disponibles");
    expect(nodeCard(DEMO, "Z_ISLA")!.note).toContain("ninguna base puede llegar");
    expect(nodeCard(DEMO, "NADA")).toBeNull();
    const lonely = {
      nodes: [{ id: "B", type: "BASE" as const, name: "B", technicians: [] }],
      edges: [],
    };
    expect(nodeCard(lonely, "B")!.note).toBe("Base sin trayectos: no puede llegar a ninguna zona.");
    const orphanEdge = {
      ...lonely,
      edges: [{ id: "E", source: "B", target: "X", weight: 1, bidirectional: true }],
    };
    expect(nodeCard(orphanEdge, "B")!.links[0]?.other).toBe("?");
  });

  it("opciones por nombre; el id solo si el nombre se repite", () => {
    const nodes = [
      { id: "A", type: "ZONE" as const, name: "Centro", technicians: [] },
      { id: "B", type: "ZONE" as const, name: "Centro", technicians: [] },
      { id: "C", type: "ZONE" as const, name: "Isla", technicians: [] },
    ];
    expect(nodeOptions(nodes).map((o) => o.label)).toEqual(["Centro (A)", "Centro (B)", "Isla"]);
  });

  it("formatos auxiliares", () => {
    expect(formatMinutes(30)).toBe("30 min");
    expect(formatMinutes(7.256)).toBe("7.26 min");
    expect(weightInRange(1440)).toBe(true);
    expect(weightInRange(0)).toBe(false);
    expect(weightInRange(Number.NaN)).toBe(false);
    expect(technicianSummary(DEMO.nodes[3]!)).toBe("—");
    expect(joinList([])).toBe("");
    expect(joinList(["A"])).toBe("A");
    expect(joinList(["A", "B", "C"])).toBe("A, B y C");
    expect(joinList(["Fuente", "Isla"])).toBe("Fuente e Isla");
    expect(joinList(["Centro", "Hípica"])).toBe("Centro e Hípica");
    expect(joinList(["Centro", "Hielo"])).toBe("Centro y Hielo");
  });
});
