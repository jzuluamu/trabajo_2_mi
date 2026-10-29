import { createContext, useContext } from "react";

import { DARK_PALETTE, LIGHT_PALETTE, type GraphPalette } from "@/lib/graph-elements";

export type ThemePreference = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export interface ThemeState {
  preference: ThemePreference;
  resolved: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
}

/** Misma clave que lee public/theme-init.js antes de pintar. */
export const THEME_STORAGE_KEY = "sc-theme";

export const ThemeContext = createContext<ThemeState>({
  preference: "system",
  resolved: "light",
  setPreference: () => undefined,
});

export const useTheme = (): ThemeState => useContext(ThemeContext);

export const useGraphPalette = (): GraphPalette =>
  useTheme().resolved === "dark" ? DARK_PALETTE : LIGHT_PALETTE;
