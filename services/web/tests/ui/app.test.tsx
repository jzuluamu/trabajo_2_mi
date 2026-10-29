import { act, screen, waitFor, within } from "@testing-library/react";

import { FakeBff } from "./fake-bff";
import { renderWithProviders } from "./render";

beforeEach(() => {
  window.history.replaceState(null, "", "/");
  localStorage.clear();
  document.documentElement.classList.remove("dark");
});

async function login(key: string) {
  const view = renderWithProviders();
  await view.user.type(await screen.findByLabelText("Clave de acceso"), key);
  await view.user.click(screen.getByRole("button", { name: "Entrar" }));
  return view;
}

describe("inicio de sesión", () => {
  it("sin sesión muestra el formulario y el estado de los servicios", async () => {
    new FakeBff().install();
    renderWithProviders();
    expect(await screen.findByRole("heading", { name: "Bienvenido" })).toBeInTheDocument();
    const status = await screen.findByRole("status", { name: "Estado del sistema" });
    expect(within(status).getByText("Todo en línea")).toBeInTheDocument();
    expect(status).toHaveAttribute("title", expect.stringContaining("routing-service: operativo"));
    expect(screen.getByRole("button", { name: "Entrar" })).toBeDisabled();
  });

  it("una clave incorrecta muestra el mensaje del contrato asociado al campo", async () => {
    new FakeBff().install();
    await login("mala");
    expect(await screen.findByRole("alert")).toHaveTextContent("API key inválida.");
    expect(screen.getByLabelText("Clave de acceso")).toHaveAttribute(
      "aria-describedby",
      "api-key-error",
    );
  });

  it("rechaza la clave interna", async () => {
    new FakeBff().install();
    await login("internal");
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Esta clave no corresponde a un usuario de la consola.",
    );
  });

  it("permite ver la clave escrita", async () => {
    new FakeBff().install();
    const { user } = renderWithProviders();
    const input = await screen.findByLabelText("Clave de acceso");
    expect(input).toHaveAttribute("type", "password");
    await user.click(screen.getByRole("button", { name: "Mostrar la clave" }));
    expect(input).toHaveAttribute("type", "text");
  });

  it("el operador ve Red y Cobertura, pero no Configurar red", async () => {
    new FakeBff().install();
    await login("oper");
    expect(await screen.findByRole("tab", { name: /Cobertura/ })).toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: /Configurar red/ })).not.toBeInTheDocument();
    expect(screen.getAllByText("Operador de atención").length).toBeGreaterThan(0);
  });

  it("el coordinador ve Configurar red y puede cerrar sesión", async () => {
    const bff = new FakeBff().install();
    const { user } = await login("coord");
    expect(await screen.findByRole("tab", { name: /Configurar red/ })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Cerrar sesión" }));
    expect(await screen.findByRole("heading", { name: "Bienvenido" })).toBeInTheDocument();
    expect(bff.role).toBeNull();
  });

  it("si la sesión caduca durante el uso, vuelve al inicio de sesión", async () => {
    const bff = new FakeBff({ role: "operator" }).install();
    bff.failures.set("GET /api/network/network", {
      status: 401,
      code: "UNAUTHENTICATED",
      message: "Inicie sesión con su API key.",
    });
    renderWithProviders();
    expect(await screen.findByRole("heading", { name: "Bienvenido" })).toBeInTheDocument();
  });
});

describe("estado de los servicios y errores", () => {
  it("indica el servicio caído con texto, no solo con color", async () => {
    const bff = new FakeBff({ role: "operator" }).install();
    bff.services[1] = { name: "routing-service", status: "down" };
    renderWithProviders();
    expect((await screen.findAllByText("Consultas: sin conexión")).length).toBeGreaterThan(0);
    expect(screen.queryByText("Todo en línea")).not.toBeInTheDocument();
  });

  it("si la consola no responde, ofrece reintentar", async () => {
    const bff = new FakeBff({ role: "operator" }).install();
    bff.offline = true;
    const { user } = renderWithProviders();
    expect(await screen.findByText("No fue posible contactar la consola.")).toBeInTheDocument();
    bff.offline = false;
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("tab", { name: /Red/ })).toBeInTheDocument();
  });

  it("un error al leer la red se muestra con reintentar", async () => {
    const bff = new FakeBff({ role: "operator" }).install();
    bff.failures.set("GET /api/network/network", {
      status: 503,
      code: "SERVICE_UNAVAILABLE",
      message: "No fue posible contactar network-service.",
    });
    const { user } = renderWithProviders();
    expect(
      await screen.findByText("No fue posible contactar network-service."),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Reintentar" }));
    expect(await screen.findByRole("heading", { name: "Red de cobertura" })).toBeInTheDocument();
  });
});

describe("navegación y tema", () => {
  it("abre la pestaña indicada en la URL y la actualiza al cambiar", async () => {
    new FakeBff({ role: "coordinator" }).install();
    window.history.replaceState(null, "", "/#cobertura");
    const { user } = renderWithProviders();
    expect(
      await screen.findByRole("heading", { name: "¿Hasta dónde llega una base?" }),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("tab", { name: /Configurar red/ }));
    expect(window.location.hash).toBe("#configurar");
    act(() => {
      window.history.replaceState(null, "", "/#red");
      window.dispatchEvent(new HashChangeEvent("hashchange"));
    });
    expect(await screen.findByRole("heading", { name: "Red de cobertura" })).toBeInTheDocument();
  });

  it("ignora una pestaña que el rol no tiene", async () => {
    new FakeBff({ role: "operator" }).install();
    window.history.replaceState(null, "", "/#configurar");
    renderWithProviders();
    expect(await screen.findByRole("heading", { name: "Red de cobertura" })).toBeInTheDocument();
  });

  it("cambia a tema oscuro y lo recuerda", async () => {
    new FakeBff().install();
    const { user } = renderWithProviders();
    await user.click(await screen.findByRole("button", { name: "Cambiar tema" }));
    await user.click(await screen.findByRole("menuitemradio", { name: "Oscuro" }));
    await waitFor(() => {
      expect(document.documentElement).toHaveClass("dark");
    });
    expect(localStorage.getItem("sc-theme")).toBe("dark");
  });
});
