import { Circle, CircleDashed, Spline, Square, type LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import type { Kpi } from "@/lib/network-format";
import { cn } from "@/lib/utils";

/** Icono de cada indicador: la misma forma que en el mapa (cuadrado base, círculo zona). */
const ICONS: Record<string, LucideIcon> = {
  Bases: Square,
  Zonas: Circle,
  Trayectos: Spline,
  "Zonas sin conexión": CircleDashed,
};

/** "Zonas sin conexión" es un aviso: va en ámbar cuando hay alguna; el resto, con la marca. */
function tone(kpi: Kpi): string {
  return kpi.label === "Zonas sin conexión" && kpi.value > 0
    ? "bg-warning-soft text-warning"
    : "bg-brand-soft text-brand";
}

export function KpiGrid({ kpis }: { kpis: Kpi[] }) {
  return (
    <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {kpis.map((kpi) => {
        const Icon = ICONS[kpi.label] ?? Circle;
        return (
          <Card key={kpi.label} className="relative gap-1 px-4 py-4 sm:pl-[4.25rem]">
            <dt className="text-sm text-muted-foreground">
              <span
                className={cn(
                  "absolute top-4 left-4 hidden size-10 place-items-center rounded-lg sm:grid",
                  tone(kpi),
                )}
                aria-hidden
              >
                <Icon className="size-5" />
              </span>
              {kpi.label}
            </dt>
            <dd className="text-2xl font-semibold tracking-tight text-ink tabular-nums dark:text-foreground">
              {kpi.value}
            </dd>
            <dd className="text-xs text-muted-foreground">{kpi.help}</dd>
          </Card>
        );
      })}
    </dl>
  );
}
