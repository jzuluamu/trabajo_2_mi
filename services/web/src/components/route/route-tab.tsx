import { useMutation } from "@tanstack/react-query";
import { ArrowDownUp, ChevronDown, Loader2, Route as RouteIcon } from "lucide-react";
import { useMemo, useState, type SubmitEvent } from "react";

import { FormError, SelectField } from "@/components/form-fields";
import { GraphLegend } from "@/components/graph-legend";
import { NetworkGraph } from "@/components/network-graph";
import { AttentionResult, RouteResult } from "@/components/route/route-result";
import { SectionHeader } from "@/components/section-header";
import { EmptyState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { api } from "@/lib/api";
import { nodesOfType } from "@/lib/coverage-format";
import { describeError, nodeOptions } from "@/lib/network-format";
import { attentionOverlay, attentionSummary, routeOverlay, routeSummary } from "@/lib/route-format";
import type { Network } from "@/lib/types";

type Mode = "route" | "attention";

interface RouteQuery {
  origin: string;
  destination: string;
  trace: boolean;
}

interface AttentionQuery {
  zone: string;
  trace: boolean;
}

/** El valor elegido si sigue existiendo en la red; si no, el primero de la lista. */
const pick = (value: string | null, ids: string[], fallback = 0): string =>
  value !== null && ids.includes(value) ? value : (ids[fallback] ?? ids[0] ?? "");

function TraceCheckbox({
  id,
  checked,
  onChange,
}: {
  id: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <Checkbox
        id={id}
        checked={checked}
        onCheckedChange={(value) => {
          onChange(value === true);
        }}
      />
      <Label htmlFor={id} className="font-normal">
        Incluir el cálculo paso a paso
      </Label>
    </div>
  );
}

/** Menor costo (F3): la ruta más rápida entre dos lugares y la mejor base para una zona. */
export function RouteTab({ network }: { network: Network }) {
  const bases = nodesOfType(network, "BASE");
  const zones = nodesOfType(network, "ZONE");
  const allIds = network.nodes.map((node) => node.id);
  const [mode, setMode] = useState<Mode>("route");
  const [origin, setOrigin] = useState<string | null>(null);
  const [destination, setDestination] = useState<string | null>(null);
  const [zone, setZone] = useState<string | null>(null);
  const [routeTrace, setRouteTrace] = useState(false);
  const [attentionTrace, setAttentionTrace] = useState(false);

  const routeQuery = useMutation({
    mutationFn: (q: RouteQuery) => api.cheapestRoute(q.origin, q.destination, q.trace),
  });
  const attentionQuery = useMutation({
    mutationFn: (q: AttentionQuery) => api.bestAttention(q.zone, q.trace),
  });

  const firstBase = bases[0]?.id ?? null;
  const chosenOrigin = pick(origin ?? firstBase, allIds);
  const firstZone = zones.find((z) => z.id !== chosenOrigin)?.id ?? null;
  const chosenDestination = pick(destination ?? firstZone, allIds, 1);
  const chosenZone = pick(
    zone,
    zones.map((z) => z.id),
  );

  const route = routeQuery.data;
  const attention = attentionQuery.data;
  const routeLayer = useMemo(() => (route ? routeOverlay(network, route) : null), [network, route]);
  const attentionLayer = useMemo(
    () => (attention ? attentionOverlay(network, attention) : null),
    [network, attention],
  );
  const overlay = mode === "route" ? routeLayer : attentionLayer;
  const summary =
    mode === "route"
      ? route && routeSummary(network, route)
      : attention && attentionSummary(network, attention);

  const submitRoute = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    routeQuery.mutate({ origin: chosenOrigin, destination: chosenDestination, trace: routeTrace });
  };
  const submitAttention = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    attentionQuery.mutate({ zone: chosenZone, trace: attentionTrace });
  };

  return (
    <section aria-labelledby="route-heading" className="space-y-6">
      <SectionHeader
        id="route-heading"
        title="¿Cuál es la ruta más rápida?"
        description="Elija de dónde sale y a dónde va: el mapa marca el camino que toma menos minutos."
      />
      {network.nodes.length < 2 ? (
        <EmptyState
          icon={RouteIcon}
          title="Faltan lugares para trazar una ruta"
          description="Cuando la red tenga al menos dos lugares conectados (o se cargue la red de ejemplo) podrá buscar rutas aquí."
        />
      ) : (
        <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
          <div className="space-y-4">
            <Card className="h-fit">
              <CardContent>
                <Tabs
                  value={mode}
                  onValueChange={(value) => {
                    setMode(value as Mode);
                  }}
                  className="gap-5"
                >
                  <TabsList
                    aria-label="¿Qué quiere buscar?"
                    className="grid w-full grid-cols-2 group-data-[orientation=horizontal]/tabs:h-auto"
                  >
                    <TabsTrigger value="route" className="h-9 whitespace-normal">
                      Entre dos lugares
                    </TabsTrigger>
                    <TabsTrigger value="attention" className="h-9 whitespace-normal">
                      Mejor base
                    </TabsTrigger>
                  </TabsList>
                  <TabsContent value="route">
                    <form className="grid gap-4" onSubmit={submitRoute}>
                      <SelectField
                        id="route-origin"
                        label="Desde"
                        value={chosenOrigin}
                        onValueChange={setOrigin}
                        options={nodeOptions(network.nodes)}
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="h-9 justify-self-center text-muted-foreground"
                        onClick={() => {
                          setOrigin(chosenDestination);
                          setDestination(chosenOrigin);
                        }}
                      >
                        <ArrowDownUp aria-hidden />
                        Invertir el sentido
                      </Button>
                      <SelectField
                        id="route-destination"
                        label="Hasta"
                        value={chosenDestination}
                        onValueChange={setDestination}
                        options={nodeOptions(network.nodes)}
                      />
                      <TraceCheckbox
                        id="route-trace"
                        checked={routeTrace}
                        onChange={setRouteTrace}
                      />
                      <Button type="submit" disabled={routeQuery.isPending}>
                        {routeQuery.isPending && <Loader2 className="animate-spin" aria-hidden />}
                        Ver ruta
                      </Button>
                      <FormError
                        id="route-error"
                        message={routeQuery.error ? describeError(routeQuery.error) : null}
                      />
                    </form>
                  </TabsContent>
                  <TabsContent value="attention">
                    {zones.length === 0 ? (
                      <p className="text-sm text-muted-foreground">No hay zonas registradas.</p>
                    ) : (
                      <form className="grid gap-4" onSubmit={submitAttention}>
                        <SelectField
                          id="attention-zone"
                          label="Zona a atender"
                          value={chosenZone}
                          onValueChange={setZone}
                          options={nodeOptions(zones)}
                        />
                        <p className="text-xs text-pretty text-muted-foreground">
                          Solo cuentan las bases con al menos un técnico disponible.
                        </p>
                        <TraceCheckbox
                          id="attention-trace"
                          checked={attentionTrace}
                          onChange={setAttentionTrace}
                        />
                        <Button type="submit" disabled={attentionQuery.isPending}>
                          {attentionQuery.isPending && (
                            <Loader2 className="animate-spin" aria-hidden />
                          )}
                          Buscar base
                        </Button>
                        <FormError
                          id="attention-error"
                          message={
                            attentionQuery.error ? describeError(attentionQuery.error) : null
                          }
                        />
                      </form>
                    )}
                  </TabsContent>
                </Tabs>
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
                  Se suman los <strong className="font-medium text-foreground">minutos</strong> de
                  cada trayecto y se elige el camino con el total más bajo, respetando el sentido de
                  cada trayecto. El cálculo es el algoritmo de Dijkstra.
                </p>
                <p>
                  Por eso la ruta más rápida puede tener más tramos que otra: el mapa muestra
                  punteado el camino de menos tramos cuando es distinto.
                </p>
              </CollapsibleContent>
            </Collapsible>
          </div>
          <div className="min-w-0 space-y-6">
            {summary && (
              <p className="text-lg font-medium tracking-tight text-pretty" role="status">
                {summary}
              </p>
            )}
            <Card className="gap-0 overflow-hidden py-0">
              <NetworkGraph
                network={network}
                route={overlay}
                label={summary ? `Mapa de la ruta. ${summary}` : undefined}
              />
              <GraphLegend
                mode={overlay ? "route" : "network"}
                alternative={(overlay?.alternative.length ?? 0) > 0}
              />
            </Card>
            {mode === "route" && route ? (
              <RouteResult network={network} report={route} overlay={routeLayer} />
            ) : mode === "attention" && attention ? (
              <AttentionResult network={network} report={attention} overlay={attentionLayer} />
            ) : (
              <p className="text-sm text-muted-foreground">
                Al buscar, el mapa pinta la ruta en azul con los minutos acumulados en cada parada.
              </p>
            )}
          </div>
        </div>
      )}
    </section>
  );
}
