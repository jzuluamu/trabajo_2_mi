import type { CSSProperties } from "react";

import { useGraphPalette } from "@/hooks/use-theme";
import { cn } from "@/lib/utils";

interface LegendItem {
  label: string;
  shape: "square" | "circle" | "arrow";
  style: CSSProperties;
}

/** Leyenda del mapa: forma + texto, para que nada dependa solo del color. */
export function GraphLegend({ mode = "network" }: { mode?: "network" | "coverage" }) {
  const p = useGraphPalette();
  const items: LegendItem[] =
    mode === "network"
      ? [
          { label: "Base con técnico libre", shape: "square", style: { backgroundColor: p.base } },
          {
            label: "Base sin técnicos libres",
            shape: "square",
            style: { backgroundColor: p.baseIdle },
          },
          {
            label: "Zona",
            shape: "circle",
            style: { backgroundColor: p.zoneFill, borderColor: p.zoneBorder },
          },
          {
            label: "Zona sin conexión",
            shape: "circle",
            style: { backgroundColor: p.greyFill, borderColor: p.grey, borderStyle: "dashed" },
          },
          { label: "Solo ida", shape: "arrow", style: { color: p.edgeLabel } },
        ]
      : [
          {
            label: "Base de origen",
            shape: "square",
            style: { backgroundColor: p.accent, borderColor: p.amber, borderWidth: 3 },
          },
          ...p.hops.map((color, index): LegendItem => ({
            label: index === 3 ? "4+ tramos" : `${index + 1} ${index ? "tramos" : "tramo"}`,
            shape: "circle",
            style: { backgroundColor: color, borderColor: color },
          })),
          {
            label: "Sin cobertura",
            shape: "circle",
            style: { backgroundColor: p.greyFill, borderColor: p.grey, borderStyle: "dashed" },
          },
        ];
  return (
    <ul
      aria-label="Leyenda del mapa"
      className="flex flex-wrap gap-x-4 gap-y-2 border-t px-4 py-3 text-xs text-muted-foreground"
    >
      {items.map((item) => (
        <li key={item.label} className="flex items-center gap-1.5">
          {item.shape === "arrow" ? (
            <span aria-hidden className="font-mono text-sm leading-none" style={item.style}>
              →
            </span>
          ) : (
            <span
              aria-hidden
              className={cn(
                "inline-block size-3 border-2 border-transparent",
                item.shape === "square" ? "rounded-[3px]" : "rounded-full",
              )}
              style={item.style}
            />
          )}
          {item.label}
        </li>
      ))}
    </ul>
  );
}
