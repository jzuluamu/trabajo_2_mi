import { ChevronDown } from "lucide-react";

import { DataTable } from "@/components/data-table";
import { Button } from "@/components/ui/button";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { formatMinutes, senseLabel, technicianSummary, TYPE_LABELS } from "@/lib/network-format";
import type { Network, NetworkEdge, NetworkNode } from "@/lib/types";

export function NetworkTables({ network }: { network: Network }) {
  return (
    <Collapsible className="space-y-4">
      <CollapsibleTrigger asChild>
        <Button variant="outline" className="group">
          <ChevronDown
            className="transition-transform duration-200 group-data-[state=open]:rotate-180 motion-reduce:transition-none"
            aria-hidden
          />
          Ver como tabla (accesible)
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent className="space-y-6">
        <section className="space-y-2">
          <h3 className="text-sm font-medium">Bases y zonas ({network.nodes.length})</h3>
          <DataTable<NetworkNode>
            caption="Bases y zonas"
            rows={network.nodes}
            rowKey={(node) => node.id}
            columns={[
              { header: "ID", cell: (node) => <span className="font-mono">{node.id}</span> },
              { header: "Tipo", cell: (node) => TYPE_LABELS[node.type] },
              { header: "Nombre", cell: (node) => node.name },
              { header: "Técnicos", cell: technicianSummary },
            ]}
          />
        </section>
        {network.edges.length > 0 && (
          <section className="space-y-2">
            <h3 className="text-sm font-medium">
              Conexiones ({network.edges.length}) — minutos de traslado
            </h3>
            <DataTable<NetworkEdge>
              caption="Conexiones"
              rows={network.edges}
              rowKey={(edge) => edge.id}
              columns={[
                { header: "ID", cell: (edge) => <span className="font-mono">{edge.id}</span> },
                { header: "Origen", cell: (edge) => edge.source },
                { header: "Destino", cell: (edge) => edge.target },
                { header: "Minutos", numeric: true, cell: (edge) => formatMinutes(edge.weight) },
                { header: "Sentido", cell: senseLabel },
              ]}
            />
          </section>
        )}
      </CollapsibleContent>
    </Collapsible>
  );
}
