import { Building2, ChevronDown, CircleCheck, MapPin, TriangleAlert } from "lucide-react";

import { DataTable } from "@/components/data-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { reachableRows, traceRows, unreachableRows, type TraceRow } from "@/lib/coverage-format";
import type { CoverageReport, Network, ZoneCheck } from "@/lib/types";

const TRACE_ACTIONS: Record<string, string> = { Visita: "Se visita", Encola: "Se agrega a la fila" };

function ZoneVerdict({ zone, name, origin }: { zone: ZoneCheck; name: string; origin: string }) {
  const hops = zone.hops ?? 0;
  return (
    <Alert variant={zone.covered ? "success" : "warning"} role="status">
      {zone.covered ? <CircleCheck aria-hidden /> : <TriangleAlert aria-hidden />}
      <AlertTitle>{zone.covered ? `${name} está cubierta` : `${name} no está cubierta`}</AlertTitle>
      <AlertDescription>
        {zone.covered
          ? `Se llega desde ${origin} en ${hops} ${hops === 1 ? "tramo" : "tramos"}.`
          : `No hay ningún camino desde ${origin} hasta ${name}.`}
      </AlertDescription>
    </Alert>
  );
}

export function CoverageResult({ network, report }: { network: Network; report: CoverageReport }) {
  const names = new Map(network.nodes.map((node) => [node.id, node.name]));
  const nameOf = (id: string) => names.get(id) ?? id;
  const reachable = reachableRows(network, report);
  const unreachable = unreachableRows(network, report);
  const trace = traceRows(report);
  const byHops = new Map<number, typeof reachable>();
  for (const row of reachable) byHops.set(row.hops, [...(byHops.get(row.hops) ?? []), row]);

  return (
    <div className="space-y-6">
      {report.zone && (
        <ZoneVerdict zone={report.zone} name={nameOf(report.zone.id)} origin={nameOf(report.base)} />
      )}

      <section className="space-y-3" aria-labelledby="reachable-title">
        <h3 id="reachable-title" className="text-sm font-medium">
          Lugares a su alcance ({reachable.length})
        </h3>
        {reachable.length ? (
          <ul className="divide-y rounded-xl border bg-card">
            {[...byHops].map(([hops, rows]) => (
              <li key={hops} className="flex flex-col gap-2 px-4 py-3 sm:flex-row sm:items-center">
                <span className="w-24 shrink-0 text-sm text-muted-foreground tabular-nums">
                  A {hops} {hops === 1 ? "tramo" : "tramos"}
                </span>
                <ul className="flex flex-wrap gap-1.5" aria-label={`A ${hops} tramos`}>
                  {rows.map((row) => (
                    <li key={row.id}>
                      <Badge variant="outline" className="gap-1 px-2.5 py-1 text-sm font-normal">
                        {row.type === "Base" ? (
                          <Building2 aria-hidden className="text-muted-foreground" />
                        ) : (
                          <MapPin aria-hidden className="text-muted-foreground" />
                        )}
                        {row.name}
                        {row.type === "Base" && <span className="sr-only"> (base)</span>}
                      </Badge>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-muted-foreground">
            Esta base no tiene trayectos hacia ninguna zona.
          </p>
        )}
      </section>

      {unreachable.length > 0 && (
        <section className="space-y-3" aria-labelledby="unreachable-title">
          <h3 id="unreachable-title" className="text-sm font-medium">
            Zonas sin cobertura ({unreachable.length})
          </h3>
          <ul className="flex flex-wrap gap-1.5">
            {unreachable.map((row) => (
              <li key={row.id}>
                <Badge variant="warning" className="px-2.5 py-1 text-sm font-normal">
                  {row.name}
                </Badge>
              </li>
            ))}
          </ul>
          <p className="text-xs text-muted-foreground">
            Ningún camino desde esta base llega a ellas. No es un error: así está la red hoy.
          </p>
        </section>
      )}

      {trace.length > 0 && (
        <Collapsible className="space-y-2">
          <CollapsibleTrigger asChild>
            <Button variant="outline" size="sm" className="group">
              <ChevronDown
                className="transition-transform duration-200 group-data-[state=open]:rotate-180 motion-reduce:transition-none"
                aria-hidden
              />
              Ver el recorrido paso a paso ({trace.length} pasos)
            </Button>
          </CollapsibleTrigger>
          <CollapsibleContent>
            <DataTable<TraceRow>
              caption="Recorrido paso a paso"
              rows={trace}
              rowKey={(row) => String(row.step)}
              columns={[
                { header: "Paso", numeric: true, cell: (row) => row.step },
                { header: "Qué pasa", cell: (row) => TRACE_ACTIONS[row.action] ?? row.action },
                { header: "Lugar", cell: (row) => nameOf(row.node) },
                { header: "Tramos", numeric: true, cell: (row) => row.hops },
                { header: "Llega desde", cell: (row) => (row.from ? nameOf(row.from) : "—") },
              ]}
            />
          </CollapsibleContent>
        </Collapsible>
      )}
    </div>
  );
}
