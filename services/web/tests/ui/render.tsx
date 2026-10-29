import { QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import type { Core } from "cytoscape";
import type { ReactElement, ReactNode } from "react";

import { App } from "@/App";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { createQueryClient } from "@/lib/query-client";

export function renderWithProviders(ui: ReactElement = <App />) {
  const client = createQueryClient({ retry: false });
  const user = userEvent.setup();
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={client}>
      <ThemeProvider>
        <TooltipProvider delayDuration={0}>
          {children}
          <Toaster />
        </TooltipProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
  const view = render(ui, { wrapper });
  return { ...view, user, client };
}

/** Elige una opción de un Select de Radix por su etiqueta visible. */
export async function choose(user: UserEvent, field: string | RegExp, option: string | RegExp) {
  await user.click(screen.getByRole("combobox", { name: field }));
  await user.click(await screen.findByRole("option", { name: option }));
}

/** Instancia de Cytoscape (headless) creada por el último NetworkGraph montado. */
export function lastCy(): Core {
  const cy = (globalThis as { __cy?: Core }).__cy;
  if (!cy) throw new Error("No se montó ningún mapa");
  return cy;
}
