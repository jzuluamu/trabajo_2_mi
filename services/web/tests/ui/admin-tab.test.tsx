import { fireEvent, screen, within } from "@testing-library/react";

import { DEMO } from "../fixtures";
import { FakeBff } from "./fake-bff";
import { choose, lastCy, renderWithProviders } from "./render";

beforeEach(() => {
  window.history.replaceState(null, "", "/#configurar");
});

async function openAdmin({ empty = false } = {}) {
  const bff = new FakeBff({ role: "coordinator", empty }).install();
  const view = renderWithProviders();
  await screen.findByRole("heading", { name: "Configurar red" });
  return { ...view, bff };
}

describe("Nueva conexión", () => {
  it("propone el id, dibuja la vista previa y muestra el INVALID_WEIGHT del contrato", async () => {
    const { user } = await openAdmin();
    expect(screen.getByLabelText("Identificador")).toHaveValue("E10");
    await choose(user, "Hasta", "Isla");
    const minutes = screen.getByLabelText("¿Cuántos minutos toma el trayecto?");
    await user.clear(minutes);
    await user.type(minutes, "-5");
    expect(screen.getByText(/Debe ser mayor que 0 y como máximo 1440 minutos/)).toBeInTheDocument();
    const draft = lastCy().getElementById("__draft__");
    expect(draft.hasClass("invalid")).toBe(true);
    expect(draft.data("label")).toBe("revisar");
    await user.click(screen.getByRole("button", { name: "Guardar conexión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "El peso de la conexión 'E10' debe ser mayor que 0 y menor o igual a 1440 minutos.",
    );
  });

  it("guarda una conexión de solo ida, avisa con nombres y actualiza el mapa", async () => {
    const { user, bff } = await openAdmin();
    await choose(user, "Hasta", "Isla");
    const minutes = screen.getByLabelText("¿Cuántos minutos toma el trayecto?");
    await user.clear(minutes);
    await user.type(minutes, "12");
    await user.click(screen.getByRole("radio", { name: /Solo ida/ }));
    expect(lastCy().getElementById("__draft__").data("label")).toBe("12 min · vista previa");
    expect(lastCy().getElementById("__draft__").hasClass("oneway")).toBe(true);
    const id = screen.getByLabelText("Identificador");
    await user.clear(id);
    await user.type(id, "e_nueva");
    await user.click(screen.getByRole("button", { name: "Guardar conexión" }));
    expect(
      await screen.findByText("Listo: se conectó Base Norte con Isla (12 min)."),
    ).toBeInTheDocument();
    expect(bff.last("POST", "/bff/api/network/edges")?.body).toEqual({
      id: "E_NUEVA",
      source: "B_NORTE",
      target: "Z_ISLA",
      weight: 12,
      bidirectional: false,
    });
    await vi.waitFor(() => {
      expect(lastCy().getElementById("E_NUEVA").length).toBe(1);
    });
    expect(screen.getByLabelText("Identificador")).toHaveValue("E10");
  });

  it("pide los minutos y dos lugares distintos", async () => {
    const { user } = await openAdmin();
    await user.clear(screen.getByLabelText("¿Cuántos minutos toma el trayecto?"));
    expect(lastCy().getElementById("__draft__").length).toBe(0);
    await user.click(screen.getByRole("button", { name: "Guardar conexión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Escriba cuántos minutos toma el trayecto.",
    );
    await choose(user, "Hasta", "Base Norte");
    await user.click(screen.getByRole("button", { name: "Guardar conexión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Elija dos lugares distintos.");
  });

  it("con menos de dos lugares pide agregarlos primero", async () => {
    const { user } = await openAdmin({ empty: true });
    await user.click(screen.getByRole("button", { name: "Guardar conexión" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Primero agregue al menos dos lugares (bases o zonas).",
    );
  });
});

describe("Nueva base o zona", () => {
  it("propone el identificador desde el nombre y asigna ids a los técnicos", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Nueva base o zona" }));
    await user.type(screen.getByLabelText("Nombre"), "Base Este");
    expect(screen.getByLabelText("Identificador")).toHaveValue("B_ESTE");
    await user.type(screen.getByLabelText("Nombre del técnico 1"), "Sara");
    await user.click(screen.getByRole("button", { name: "Agregar técnico" }));
    await user.type(screen.getByLabelText("Nombre del técnico 2"), "Juan");
    await user.click(screen.getByRole("switch", { name: "Técnico 2 disponible" }));
    expect(screen.getByText("Ocupado")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Agregar técnico" }));
    await user.click(screen.getByRole("button", { name: "Quitar técnico 3" }));
    await user.click(screen.getByRole("button", { name: "Agregar base" }));
    expect(await screen.findByText("Listo: se agregó Base Este.")).toBeInTheDocument();
    expect(bff.last("POST", "/bff/api/network/nodes")?.body).toEqual({
      id: "B_ESTE",
      type: "BASE",
      name: "Base Este",
      technicians: [
        { id: "T05", name: "Sara", available: true },
        { id: "T06", name: "Juan", available: false },
      ],
    });
    expect(screen.getByLabelText("Nombre")).toHaveValue("");
    expect(screen.getByRole("button", { name: "Quitar técnico 1" })).toBeDisabled();
  });

  it("permite cambiar el identificador y muestra el DUPLICATE_ID del contrato", async () => {
    const { user } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Nueva base o zona" }));
    await user.type(screen.getByLabelText("Nombre"), "Otra");
    const id = screen.getByLabelText("Identificador");
    await user.clear(id);
    await user.type(id, "b_norte");
    await user.click(screen.getByRole("button", { name: "Agregar base" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ya existe un nodo con id 'B_NORTE'.",
    );
  });

  it("pide el nombre antes de enviar", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Nueva base o zona" }));
    await user.click(screen.getByRole("button", { name: "Agregar base" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Escriba el nombre.");
    expect(bff.last("POST", "/bff/api/network/nodes")).toBeUndefined();
  });

  it("una zona no lleva técnicos", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Nueva base o zona" }));
    await user.click(screen.getByRole("radio", { name: /Zona/ }));
    expect(screen.queryByText("Técnicos de la base")).not.toBeInTheDocument();
    await user.type(screen.getByLabelText("Nombre"), "Las Palmas");
    expect(screen.getByLabelText("Identificador")).toHaveValue("Z_LAS_PALMAS");
    await user.click(screen.getByRole("button", { name: "Agregar zona" }));
    expect(await screen.findByText("Listo: se agregó Las Palmas.")).toBeInTheDocument();
    expect(bff.last("POST", "/bff/api/network/nodes")?.body).toEqual({
      id: "Z_LAS_PALMAS",
      type: "ZONE",
      name: "Las Palmas",
    });
  });
});

describe("Eliminar", () => {
  it("un lugar con conexiones no se puede eliminar y se dice cuáles borrar antes", async () => {
    const { user } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Eliminar" }));
    expect(
      screen.getByText(
        "Antes elimine sus 2 conexiones: Base Norte ↔ Centro · 30 min y Base Norte ↔ Alameda · 5 min.",
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Eliminar lugar" })).toBeDisabled();
    await choose(user, "Lugar", "Fuente");
    expect(
      screen.getByText("Antes elimine su conexión: Base Oeste ↔ Fuente · 6 min."),
    ).toBeInTheDocument();
  });

  it("muestra el error del contrato si la red cambió mientras tanto", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Eliminar" }));
    await choose(user, "Lugar", "Isla");
    bff.failures.set("DELETE /api/network/nodes/Z_ISLA", {
      status: 409,
      code: "NODE_IN_USE",
      message: "El nodo 'Z_ISLA' tiene conexiones; elimínelas primero.",
    });
    await user.click(screen.getByRole("button", { name: "Eliminar lugar" }));
    const dialog = await screen.findByRole("alertdialog", { name: "¿Eliminar Isla?" });
    await user.click(within(dialog).getByRole("button", { name: "Eliminar lugar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("tiene conexiones");
  });

  it("cancelar no borra nada", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Eliminar" }));
    await user.click(screen.getByRole("button", { name: "Eliminar conexión" }));
    await user.click(await screen.findByRole("button", { name: "Cancelar" }));
    expect(bff.last("DELETE", "/bff/api/network/edges")).toBeUndefined();
  });

  it("elimina la conexión elegida y luego el lugar que quedó libre", async () => {
    const { user, bff } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Eliminar" }));
    await choose(user, "Conexión", "Base Oeste ↔ Fuente · 6 min");
    await user.click(screen.getByRole("button", { name: "Eliminar conexión" }));
    const edgeDialog = await screen.findByRole("alertdialog", {
      name: "¿Eliminar Base Oeste ↔ Fuente · 6 min?",
    });
    await user.click(within(edgeDialog).getByRole("button", { name: "Eliminar conexión" }));
    expect(
      await screen.findByText("Se eliminó la conexión Base Oeste ↔ Fuente · 6 min."),
    ).toBeInTheDocument();
    await choose(user, "Lugar", "Base Oeste");
    await user.click(screen.getByRole("button", { name: "Eliminar lugar" }));
    await user.click(
      within(await screen.findByRole("alertdialog")).getByRole("button", {
        name: "Eliminar lugar",
      }),
    );
    expect(await screen.findByText("Se eliminó Base Oeste.")).toBeInTheDocument();
    expect(bff.network.nodes.some((n) => n.id === "B_OESTE")).toBe(false);
  });

  it("sin conexiones ni lugares, los botones quedan deshabilitados", async () => {
    const { user } = await openAdmin({ empty: true });
    await user.click(screen.getByRole("tab", { name: "Eliminar" }));
    expect(screen.getByRole("button", { name: "Eliminar lugar" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Eliminar conexión" })).toBeDisabled();
  });
});

describe("Cargar archivo", () => {
  const file = (content: string) => new File([content], "red.json", { type: "application/json" });

  it("pide un archivo", async () => {
    const { user } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Cargar archivo" }));
    await user.click(screen.getByRole("button", { name: "Cargar red" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Elija un archivo para cargar.");
  });

  it("rechaza un archivo que no es JSON", async () => {
    const { user } = await openAdmin();
    await user.click(screen.getByRole("tab", { name: "Cargar archivo" }));
    await user.upload(screen.getByLabelText("Archivo de la red"), file("{no json"));
    expect(screen.getByText("red.json")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cargar red" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("El archivo no es un JSON válido.");
  });

  it("acepta un archivo soltado y reemplaza la red", async () => {
    const { user, bff } = await openAdmin({ empty: true });
    await user.click(screen.getByRole("tab", { name: "Cargar archivo" }));
    const zone = screen.getByText("Arrastre el archivo aquí o haga clic para elegirlo");
    const dropTarget = zone.closest("label")!;
    fireEvent.dragOver(dropTarget);
    fireEvent.dragLeave(dropTarget);
    fireEvent.drop(dropTarget, { dataTransfer: { files: [file(JSON.stringify(DEMO))] } });
    expect(screen.getByText("red.json")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cargar red" }));
    expect(await screen.findByText("Red cargada: 11 lugares y 9 conexiones.")).toBeInTheDocument();
    expect(bff.network.nodes).toHaveLength(11);
  });

  it("puede agregar sin reemplazar y muestra el error con su ubicación en el archivo", async () => {
    const { user, bff } = await openAdmin();
    bff.failures.set("POST /api/network/network/import", {
      status: 409,
      code: "DUPLICATE_ID",
      message: "Ya existe un nodo con id 'B_NORTE'.",
      details: { section: "nodes", index: 0 },
    });
    await user.click(screen.getByRole("tab", { name: "Cargar archivo" }));
    await user.click(screen.getByRole("radio", { name: /Agregar/ }));
    await user.upload(screen.getByLabelText("Archivo de la red"), file(JSON.stringify(DEMO)));
    await user.click(screen.getByRole("button", { name: "Cargar red" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Ya existe un nodo con id 'B_NORTE'. (archivo: nodo #1)",
    );
    expect(
      (bff.last("POST", "/bff/api/network/network/import")?.body as { replace: boolean }).replace,
    ).toBe(false);
  });
});
