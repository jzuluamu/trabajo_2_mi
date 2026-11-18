import { ChevronDown, Clock, MapPinOff, Route as RouteIcon, TriangleAlert } from "lucide-react";

import { DataTable } from "@/components/data-table";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { formatMinutes, plural } from "@/lib/network-format";
import {
  alternativeRows,
  attentionSummary,
  dijkstraTraceRows,
  fewestHopsComparison,
  itinerary,
  routeSummary,
  type DijkstraTraceRow,
  type RouteOverlay,
} from "@/lib/route-format";
import type { AttentionReport, Network, RouteReport, TraceStep } from "@/lib/types";

/** Itinerario de la ruta: cada tramo con sus minutos y la hora de llegada acumulada. */
function Itinerary({ network, overlay }: { network: Network; overlay: RouteOverlay }) {
  const rows = itinerary(network, overlay);
  if (!rows.length) return null;
  return (
    <section className="space-y-3" aria-labelledby="itinerary-title">
      <h3 id="itinerary-title" className="text-sm font-medium">
        Recorrido ({plural(rows.length, "tramo", "tramos")})
      </h3>
      <ol aria-labelledby="itinerary-title" className="divide-y rounded-xl border bg-card">
        {rows.map((row, index) => (
          <li key={row.edgeId} className="flex items-center gap-3 px-4 py-3">
            <span
              aria-hidden
              className="grid size-7 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-ink dark:text-foreground"
            >
              {index + 1}
            </span>
            <span className="min-w-0 flex-1 text-sm">
              {row.from} → <span className="font-medium">{row.to}</span>
              <span className="block text-xs text-muted-foreground">
                {formatMinutes(row.minutes)} · conexión{" "}
                <span className="font-mono">{row.edgeId}</span>
              </span>
            </span>
            <span className="shrink-0 text-right text-sm tabular-nums">
              <span className="sr-only">Llega a los </span>
              {formatMinutes(row.arrival)}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}

function DijkstraTrace({ network, trace }: { network: Network; trace: TraceStep[] | null }) {
  const rows = dijkstraTraceRows(network, trace);
  if (!rows.length) return null;
  const withBase = rows.some((row) => row.base);
  return (
    <Collapsible className="space-y-2">
      <CollapsibleTrigger asChild>
        <Button variant="outline" size="sm" className="group">
          <ChevronDown
            className="transition-transform duration-200 group-data-[state=open]:rotate-180 motion-reduce:transition-none"
            aria-hidden
          />
          Ver el cálculo paso a paso ({rows.length} pasos)
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <DataTable<DijkstraTraceRow>
          caption="Cálculo paso a paso"
          rows={rows}
          rowKey={(row) => row.key}
          columns={[
            ...(withBase
              ? [{ header: "Desde la base", cell: (row: DijkstraTraceRow) => row.base }]
              : []),
            { header: "Paso", numeric: true, cell: (row) => row.step },
            { header: "Qué pasa", cell: (row) => row.action },
            { header: "Lugar", cell: (row) => row.node },
            { header: "Minutos", numeric: true, cell: (row) => row.minutes },
            { header: "Llega desde", cell: (row) => row.from || "—" },
          ]}
        />
      </CollapsibleContent>
    </Collapsible>
  );
}

export function RouteResult({
  network,
  report,
  overlay,
}: {
  network: Network;
  report: RouteReport;
  overlay: RouteOverlay | null;
}) {
  const comparison = fewestHopsComparison(network, report);
  return (
    <div className="space-y-6">
      {!report.found ? (
        <Alert variant="warning" role="status">
          <MapPinOff aria-hidden />
          <AlertTitle>No hay ruta en ese sentido</AlertTitle>
          <AlertDescription>
            {routeSummary(network, report)} No es un error: así está la red hoy.
          </AlertDescription>
        </Alert>
      ) : (
        comparison && (
          <Alert role="note">
            <Clock aria-hidden />
            <AlertTitle>Menos tramos no siempre es más rápido</AlertTitle>
            <AlertDescription>{comparison}</AlertDescription>
          </Alert>
        )
      )}
      {overlay && <Itinerary network={network} overlay={overlay} />}
      <DijkstraTrace network={network} trace={report.trace} />
    </div>
  );
}

export function AttentionResult({
  network,
  report,
  overlay,
}: {
  network: Network;
  report: AttentionReport;
  overlay: RouteOverlay | null;
}) {
  const alternatives = alternativeRows(network, report);
  return (
    <div className="space-y-6">
      {!report.found && (
        <Alert variant="warning" role="status">
          <TriangleAlert aria-hidden />
          <AlertTitle>No se puede atender esta zona</AlertTitle>
          <AlertDescription>{attentionSummary(network, report)}</AlertDescription>
        </Alert>
      )}
      {overlay && <Itinerary network={network} overlay={overlay} />}
      {alternatives.length > 0 && (
        <section className="space-y-3" aria-labelledby="alternatives-title">
          <h3 id="alternatives-title" className="text-sm font-medium">
            Otras bases con técnico disponible ({alternatives.length})
          </h3>
          <ul className="divide-y rounded-xl border bg-card">
            {alternatives.map((row) => (
              <li key={row.id} className="flex items-center justify-between gap-3 px-4 py-3">
                <span className="flex items-center gap-2 text-sm">
                  <RouteIcon className="size-4 text-muted-foreground" aria-hidden />
                  {row.name}
                </span>
                <span className="flex items-center gap-2">
                  <Badge variant="secondary">{plural(row.hops, "tramo", "tramos")}</Badge>
                  <span className="text-sm tabular-nums">{formatMinutes(row.minutes)}</span>
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}
      <DijkstraTrace network={network} trace={report.trace} />
    </div>
  );
}
