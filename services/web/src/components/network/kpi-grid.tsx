import { Card } from "@/components/ui/card";
import type { Kpi } from "@/lib/network-format";

export function KpiGrid({ kpis }: { kpis: Kpi[] }) {
  return (
    <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
      {kpis.map((kpi) => (
        <Card key={kpi.label} className="gap-1 px-4 py-4">
          <dt className="text-sm text-muted-foreground">{kpi.label}</dt>
          <dd className="text-2xl font-semibold tracking-tight tabular-nums">{kpi.value}</dd>
          <dd className="text-xs text-muted-foreground">{kpi.help}</dd>
        </Card>
      ))}
    </dl>
  );
}
