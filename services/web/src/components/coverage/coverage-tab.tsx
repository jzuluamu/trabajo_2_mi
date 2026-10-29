import { useMutation } from "@tanstack/react-query";
import { ChevronDown, Loader2, Radar } from "lucide-react";
import { useMemo, useState, type SubmitEvent } from "react";

import { CoverageResult } from "@/components/coverage/coverage-result";
import { FormError, SelectField } from "@/components/form-fields";
import { GraphLegend } from "@/components/graph-legend";
import { NetworkGraph } from "@/components/network-graph";
import { SectionHeader } from "@/components/section-header";
import { EmptyState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Label } from "@/components/ui/label";
import { api } from "@/lib/api";
import { coverageOverlay, coverageSummary, nodesOfType } from "@/lib/coverage-format";
import { describeError, nodeOptions } from "@/lib/network-format";
import type { Network } from "@/lib/types";

const ANY_ZONE = "__all__";

interface CoverageQuery {
  base: string;
  zone: string | null;
  trace: boolean;
}

export function CoverageTab({ network }: { network: Network }) {
  const bases = nodesOfType(network, "BASE");
  const zones = nodesOfType(network, "ZONE");
  const [base, setBase] = useState<string | null>(null);
  const [zone, setZone] = useState(ANY_ZONE);
  const [trace, setTrace] = useState(false);
  const query = useMutation({
    mutationFn: ({ base: origin, zone: target, trace: withTrace }: CoverageQuery) =>
      api.coverage(origin, target, withTrace),
  });
  const report = query.data;
  const overlay = useMemo(() => (report ? coverageOverlay(report) : null), [report]);
  const chosenBase = base !== null && bases.some((b) => b.id === base) ? base : (bases[0]?.id ?? "");

  const submit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    query.mutate({ base: chosenBase, zone: zone === ANY_ZONE ? null : zone, trace });
  };

  return (
    <section aria-labelledby="coverage-heading" className="space-y-6">
      <SectionHeader
        id="coverage-heading"
        title="¿Hasta dónde llega una base?"
        description="Elija una base y vea qué zonas puede atender siguiendo los trayectos registrados."
      />
      {bases.length === 0 ? (
        <EmptyState
          icon={Radar}
          title="Todavía no hay bases"
          description="Cuando el coordinador agregue bases (o cargue la red de ejemplo) podrá consultar su cobertura aquí."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
          <div className="space-y-4">
            <Card className="h-fit">
              <CardContent>
                <form className="grid gap-4" onSubmit={submit}>
                  <SelectField
                    id="coverage-base"
                    label="Base de partida"
                    value={chosenBase}
                    onValueChange={setBase}
                    options={nodeOptions(bases)}
                  />
                  <SelectField
                    id="coverage-zone"
                    label="¿Revisar una zona en particular?"
                    value={zone}
                    onValueChange={setZone}
                    options={[{ value: ANY_ZONE, label: "No, ver todas" }, ...nodeOptions(zones)]}
                  />
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="coverage-trace"
                      checked={trace}
                      onCheckedChange={(checked) => {
                        setTrace(checked === true);
                      }}
                    />
                    <Label htmlFor="coverage-trace" className="font-normal">
                      Incluir el recorrido paso a paso
                    </Label>
                  </div>
                  <Button type="submit" disabled={query.isPending}>
                    {query.isPending && <Loader2 className="animate-spin" aria-hidden />}
                    Ver cobertura
                  </Button>
                  <FormError
                    id="coverage-error"
                    message={query.error ? describeError(query.error) : null}
                  />
                </form>
              </CardContent>
            </Card>
            <Collapsible className="rounded-xl border bg-card px-4 py-3">
              <CollapsibleTrigger className="group flex w-full items-center justify-between gap-2 text-left text-sm font-medium">
                ¿Cómo se calcula?
                <ChevronDown
                  className="size-4 text-muted-foreground transition-transform duration-200 group-data-[state=open]:rotate-180 motion-reduce:transition-none"
                  aria-hidden
                />
              </CollapsibleTrigger>
              <CollapsibleContent className="space-y-2 pt-2 text-sm text-pretty text-muted-foreground">
                <p>
                  Una zona está cubierta si existe algún camino desde la base siguiendo los
                  trayectos y respetando su sentido.
                </p>
                <p>
                  Los <strong className="font-medium text-foreground">tramos</strong> cuentan
                  cuántos trayectos hay que recorrer como mínimo, no los minutos. El cálculo es un
                  recorrido en anchura (BFS).
                </p>
              </CollapsibleContent>
            </Collapsible>
          </div>
          <div className="min-w-0 space-y-6">
            {report && (
              <p className="text-lg font-medium tracking-tight text-pretty" role="status">
                {coverageSummary(network, report)}
              </p>
            )}
            <Card className="gap-0 overflow-hidden py-0">
              <NetworkGraph
                network={network}
                coverage={overlay}
                label={report ? `Mapa de cobertura. ${coverageSummary(network, report)}` : undefined}
              />
              <GraphLegend mode={report ? "coverage" : "network"} />
            </Card>
            {report ? (
              <CoverageResult network={network} report={report} />
            ) : (
              <p className="text-sm text-muted-foreground">
                Al consultar, el mapa pinta de azul lo que la base alcanza y marca lo que queda
                fuera.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
