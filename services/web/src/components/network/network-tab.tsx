import { Network as NetworkIcon, RefreshCw } from "lucide-react";
import { useState } from "react";

import { SelectField } from "@/components/form-fields";
import { GraphLegend } from "@/components/graph-legend";
import { KpiGrid } from "@/components/network/kpi-grid";
import { NetworkTables } from "@/components/network/network-tables";
import { NodeCard } from "@/components/network/node-card";
import { NetworkGraph } from "@/components/network-graph";
import { SectionHeader } from "@/components/section-header";
import { EmptyState } from "@/components/states";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { networkKpis, nodeCard, nodeOptions } from "@/lib/network-format";
import type { Network } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NetworkTabProps {
  network: Network;
  refreshing: boolean;
  onRefresh: () => void;
  onConfigure?: () => void;
}

export function NetworkTab({ network, refreshing, onRefresh, onConfigure }: NetworkTabProps) {
  const [chosen, setChosen] = useState<string | null>(null);
  // El mapa abre sin resaltado: se ve la red completa hasta que el usuario elige un lugar.
  const [highlight, setHighlight] = useState(false);
  const ids = network.nodes.map((node) => node.id);
  const selected = chosen !== null && ids.includes(chosen) ? chosen : (ids[0] ?? null);
  const card = selected ? nodeCard(network, selected) : null;

  // Clic en un nodo: lo elige para la ficha. Clic en el fondo: el mapa vuelve a la normalidad.
  const choose = (nodeId: string | null) => {
    if (nodeId) setChosen(nodeId);
    setHighlight(nodeId !== null);
  };

  return (
    <section aria-labelledby="network-heading" className="space-y-6">
      <SectionHeader
        id="network-heading"
        title="Red de cobertura"
        description="Así está organizada la red hoy. Haga clic en un lugar del mapa para ver su detalle."
        action={
          <Button variant="outline" size="sm" onClick={onRefresh} disabled={refreshing}>
            <RefreshCw className={cn(refreshing && "animate-spin")} aria-hidden />
            Actualizar
          </Button>
        }
      />
      {network.nodes.length === 0 ? (
        <EmptyState
          icon={NetworkIcon}
          title="La red está vacía"
          description="Todavía no hay bases ni zonas. El coordinador puede agregarlas o cargar la red de ejemplo."
          action={
            onConfigure && (
              <Button size="sm" onClick={onConfigure}>
                Ir a Configurar red
              </Button>
            )
          }
        />
      ) : (
        <>
          <KpiGrid kpis={networkKpis(network)} />
          <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
            <Card className="gap-0 overflow-hidden py-0">
              <NetworkGraph
                network={network}
                selected={highlight ? selected : null}
                onSelect={choose}
              />
              <GraphLegend />
            </Card>
            <aside className="space-y-3" aria-label="Detalle del lugar">
              <SelectField
                id="card-node"
                label="Ver detalle de"
                value={selected ?? ""}
                onValueChange={choose}
                options={nodeOptions(network.nodes)}
              />
              {card && <NodeCard card={card} />}
            </aside>
          </div>
          <NetworkTables network={network} />
        </>
      )}
    </section>
  );
}
