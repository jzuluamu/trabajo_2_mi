import { ATTENTION_COLINA, DEMO, ROUTE_NORTE_CENTRO } from "../fixtures";
import { overlayFor } from "@/lib/graph-elements";
import {
  alternativeRows,
  attentionOverlay,
  attentionSummary,
  dijkstraTraceRows,
  fewestHopsComparison,
  humanize,
  itinerary,
  pathEdges,
  routeOverlay,
  routeSummary,
} from "@/lib/route-format";
import type { AttentionReport, RouteReport } from "@/lib/types";

const NO_ROUTE: RouteReport = {
  ...ROUTE_NORTE_CENTRO,
  found: false,
  destination: "Z_FUENTE",
  path: [],
  total_cost: null,
  hops: null,
  legs: [],
  fewest_hops: null,
};

describe("pathEdges", () => {
  it("encuentra cada conexión y su sentido de viaje", () => {
    expect(pathEdges(DEMO, ["B_SUR", "Z_DELICIAS", "Z_COLINA"])).toEqual([
      { id: "E06", forward: true },
      { id: "E07", forward: true },
    ]);
    // E04 va de Bosque a Centro: recorrerla de Centro a Bosque es en sentido contrario.
    expect(pathEdges(DEMO, ["Z_CENTRO", "Z_BOSQUE"])).toEqual([{ id: "E04", forward: false }]);
  });

  it("no usa al revés una conexión de solo ida", () => {
    expect(pathEdges(DEMO, ["Z_ESTACION", "Z_DELICIAS"])).toEqual([]);
    expect(pathEdges(DEMO, ["B_NORTE"])).toEqual([]);
  });
});

describe("routeOverlay e itinerario", () => {
  it("marca la ruta, los minutos acumulados y el camino de menos tramos", () => {
    const overlay = routeOverlay(DEMO, ROUTE_NORTE_CENTRO);
    expect(overlay).not.toBeNull();
    expect(overlay?.edges.map((e) => e.id)).toEqual(["E02", "E03", "E04"]);
    expect(overlay?.alternative).toEqual(["E01"]);
    expect([...(overlay?.arrivals ?? [])]).toEqual([
      ["B_NORTE", 0],
      ["Z_ALAMEDA", 5],
      ["Z_BOSQUE", 10],
      ["Z_CENTRO", 15],
    ]);
    expect(overlay && itinerary(DEMO, overlay)).toEqual([
      { edgeId: "E02", from: "Base Norte", to: "Alameda", minutes: 5, arrival: 5 },
      { edgeId: "E03", from: "Alameda", to: "Bosque", minutes: 5, arrival: 10 },
      { edgeId: "E04", from: "Bosque", to: "Centro", minutes: 5, arrival: 15 },
    ]);
  });

  it("sin ruta no hay nada que pintar", () => {
    expect(routeOverlay(DEMO, NO_ROUTE)).toBeNull();
    expect(routeOverlay(DEMO, { ...ROUTE_NORTE_CENTRO, path: [] })).toBeNull();
    expect(attentionOverlay(DEMO, { ...ATTENTION_COLINA, best: null })).toBeNull();
  });

  it("la mejor atención trae solo nodos: las conexiones salen de la red", () => {
    const overlay = attentionOverlay(DEMO, ATTENTION_COLINA);
    expect(overlay?.edges.map((e) => e.id)).toEqual(["E06", "E07"]);
    expect(overlay?.arrivals.get("Z_COLINA")).toBe(20);
    expect(overlay?.alternative).toEqual([]);
  });
});

describe("textos para el operador", () => {
  it("resume la ruta con nombres", () => {
    expect(routeSummary(DEMO, ROUTE_NORTE_CENTRO)).toBe(
      "De Base Norte a Centro: 15 min en 3 tramos, por Alameda y Bosque.",
    );
    expect(
      routeSummary(DEMO, {
        ...ROUTE_NORTE_CENTRO,
        path: ["B_NORTE", "Z_CENTRO"],
        total_cost: 30,
        hops: 1,
      }),
    ).toBe("De Base Norte a Centro: 30 min en 1 tramo, directo.");
    expect(routeSummary(DEMO, NO_ROUTE)).toBe(
      "No hay ruta de Base Norte a Fuente: ningún camino de la red los conecta en ese sentido.",
    );
    expect(routeSummary(DEMO, { ...NO_ROUTE, origin: "X_1", destination: "X_2" })).toContain(
      "de X_1 a X_2",
    );
  });

  it("compara con el camino de menos tramos solo cuando es otro", () => {
    expect(fewestHopsComparison(DEMO, ROUTE_NORTE_CENTRO)).toBe(
      "El camino de menos tramos (Base Norte → Centro, 1 tramo) tarda 30 min: esta ruta ahorra 15 min.",
    );
    const same = {
      ...ROUTE_NORTE_CENTRO,
      fewest_hops: { path: ROUTE_NORTE_CENTRO.path, hops: 3, cost: 15 },
    };
    expect(fewestHopsComparison(DEMO, same)).toBeNull();
    const tie = {
      ...ROUTE_NORTE_CENTRO,
      fewest_hops: { path: ["B_NORTE", "Z_CENTRO"], hops: 1, cost: 15 },
    };
    expect(fewestHopsComparison(DEMO, tie)).toBe(
      "El camino de menos tramos (Base Norte → Centro, 1 tramo) tarda 15 min.",
    );
    expect(fewestHopsComparison(DEMO, NO_ROUTE)).toBeNull();
  });

  it("cambia ids por nombres sin tocar ids parecidos", () => {
    expect(humanize(DEMO, "Z_FUENTE solo la alcanza (B_OESTE).")).toBe(
      "Fuente solo la alcanza (Base Oeste).",
    );
    expect(humanize(DEMO, "Z_FUENTE_2 no es Z_FUENTE")).toBe("Z_FUENTE_2 no es Fuente");
    expect(humanize({ nodes: [], edges: [] }, "B_NORTE")).toBe("B_NORTE");
  });

  it("resume la mejor atención y sus alternativas", () => {
    expect(attentionSummary(DEMO, ATTENTION_COLINA)).toBe(
      "Enviar desde Base Sur (Marta): 20 min en 2 tramos.",
    );
    const unattended: AttentionReport = {
      ...ATTENTION_COLINA,
      found: false,
      best: null,
      alternatives: [],
      message: "Z_ISLA no se puede atender: es inalcanzable desde toda base.",
    };
    expect(attentionSummary(DEMO, unattended)).toBe(
      "Isla no se puede atender: es inalcanzable desde toda base.",
    );
    const nobody = { ...ATTENTION_COLINA, best: { ...ATTENTION_COLINA.best!, technicians: [] } };
    expect(attentionSummary(DEMO, nobody)).toBe("Enviar desde Base Sur: 20 min en 2 tramos.");
    expect(alternativeRows(DEMO, ATTENTION_COLINA)).toEqual([
      { id: "B_NORTE", name: "Base Norte", minutes: 25, hops: 4 },
    ]);
  });

  it("traduce la traza de Dijkstra", () => {
    const rows = dijkstraTraceRows(DEMO, [
      { step: 1, action: "pop", node: "B_SUR", data: { cost: 0, base: "B_SUR" } },
      { step: 1, action: "relax", node: "Z_DELICIAS", data: { cost: 8, from: "B_SUR" } },
      { step: 2, action: "otra", node: "Z_DELICIAS", data: {} },
    ]);
    expect(rows[0]).toEqual({
      key: "0",
      base: "Base Sur",
      step: 1,
      action: "Se fija (ya es el más rápido)",
      node: "Base Sur",
      minutes: "0 min",
      from: "",
    });
    expect(rows[1]?.from).toBe("Base Sur");
    expect(rows[2]).toMatchObject({ action: "otra", minutes: "", base: "" });
    expect(dijkstraTraceRows(DEMO, null)).toEqual([]);
  });
});

describe("overlayFor con una ruta", () => {
  it("salida, paradas con minutos, llegada, sentido y el resto atenuado", () => {
    const route = routeOverlay(DEMO, ROUTE_NORTE_CENTRO);
    const { classes, labels } = overlayFor(DEMO, { route, selected: "Z_ISLA" });
    expect(classes.get("B_NORTE")).toEqual(["route-origin"]);
    expect(classes.get("Z_ALAMEDA")).toEqual(["on-route"]);
    expect(classes.get("Z_CENTRO")).toEqual(["route-destination"]);
    expect(classes.get("E02")).toEqual(["route"]);
    expect(classes.get("E01")).toEqual(["route-alt"]);
    expect(classes.get("E05")).toEqual(["faded"]);
    expect(classes.get("Z_ISLA")).toEqual(["faded"]);
    expect(labels.get("Z_BOSQUE")).toBe("Bosque\na 10 min");
    expect(labels.get("Z_CENTRO")).toBe("Centro\nllegada · 15 min");
  });

  it("una conexión recorrida al revés lleva la flecha del otro lado", () => {
    const route = {
      origin: "Z_CENTRO",
      destination: "Z_BOSQUE",
      path: ["Z_CENTRO", "Z_BOSQUE"],
      edges: [{ id: "E04", forward: false }],
      arrivals: new Map([
        ["Z_CENTRO", 0],
        ["Z_BOSQUE", 5],
      ]),
      alternative: [],
    };
    expect(overlayFor(DEMO, { route }).classes.get("E04")).toEqual(["route", "route-reverse"]);
  });

  it("ignora una ruta con lugares que ya no existen", () => {
    const route = { ...routeOverlay(DEMO, ROUTE_NORTE_CENTRO)!, destination: "NADA" };
    expect(overlayFor(DEMO, { route }).classes.size).toBe(0);
  });
});
