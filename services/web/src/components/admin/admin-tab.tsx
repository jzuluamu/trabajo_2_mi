import { useState } from "react";

import { DeletePanel } from "@/components/admin/delete-panel";
import { EdgeForm } from "@/components/admin/edge-form";
import { ImportPanel } from "@/components/admin/import-panel";
import { NodeForm } from "@/components/admin/node-form";
import { GraphLegend } from "@/components/graph-legend";
import { NetworkGraph } from "@/components/network-graph";
import { SectionHeader } from "@/components/section-header";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { DraftEdge } from "@/lib/graph-elements";
import type { Network } from "@/lib/types";

const ACTIONS = [
  ["edge", "Nueva conexión"],
  ["node", "Nueva base o zona"],
  ["delete", "Eliminar"],
  ["import", "Cargar archivo"],
] as const;

/** Configurar red (solo coordinador). network-service valida; aquí se muestran sus mensajes. */
export function AdminTab({ network }: { network: Network }) {
  const [draft, setDraft] = useState<DraftEdge | null>(null);
  return (
    <section aria-labelledby="admin-heading" className="space-y-6">
      <SectionHeader
        id="admin-heading"
        title="Configurar red"
        description="Agregue bases, zonas y los trayectos entre ellas. Lo que escribe aparece en el mapa antes de guardarlo."
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_26rem]">
        <Card className="order-last gap-0 overflow-hidden py-0 lg:order-none">
          <NetworkGraph network={network} draft={draft} />
          <p className="border-t px-4 py-3 text-xs text-muted-foreground">
            La línea punteada es la conexión que está escribiendo: todavía no se ha guardado.
          </p>
          <GraphLegend />
        </Card>
        <Card className="h-fit">
          <CardContent>
            <Tabs defaultValue="edge" className="gap-5">
              <TabsList
                aria-label="¿Qué desea hacer?"
                className="grid w-full grid-cols-2 group-data-[orientation=horizontal]/tabs:h-auto"
              >
                {ACTIONS.map(([value, label]) => (
                  <TabsTrigger key={value} value={value} className="h-9 whitespace-normal">
                    {label}
                  </TabsTrigger>
                ))}
              </TabsList>
              <TabsContent value="edge">
                <EdgeForm network={network} onDraftChange={setDraft} />
              </TabsContent>
              <TabsContent value="node">
                <NodeForm network={network} />
              </TabsContent>
              <TabsContent value="delete">
                <DeletePanel network={network} />
              </TabsContent>
              <TabsContent value="import">
                <ImportPanel />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </section>
  );
}
