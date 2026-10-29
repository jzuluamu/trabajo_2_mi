import { Trash2 } from "lucide-react";
import { useState } from "react";

import { FormError, SelectField } from "@/components/form-fields";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { useNetworkMutation } from "@/hooks/use-network";
import { api } from "@/lib/api";
import { describeError, formatMinutes, joinList, nodeOptions } from "@/lib/network-format";
import type { Network, NetworkEdge } from "@/lib/types";

interface ConfirmDeleteProps {
  label: string;
  title: string;
  description: string;
  disabled: boolean;
  onConfirm: () => void;
}

function ConfirmDelete({ label, title, description, disabled, onConfirm }: ConfirmDeleteProps) {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive"
          disabled={disabled}
        >
          <Trash2 aria-hidden />
          {label}
        </Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            onClick={onConfirm}
          >
            {label}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export function DeletePanel({ network }: { network: Network }) {
  const [nodeChoice, setNodeChoice] = useState<string | null>(null);
  const [edgeChoice, setEdgeChoice] = useState<string | null>(null);
  const names = new Map(network.nodes.map((node) => [node.id, node.name]));
  const nameOf = (id: string) => names.get(id) ?? id;
  const edgeLabel = (edge: NetworkEdge) =>
    `${nameOf(edge.source)} ${edge.bidirectional ? "↔" : "→"} ${nameOf(edge.target)} · ${formatMinutes(edge.weight)}`;
  const deleteNode = useNetworkMutation(api.deleteNode, (id) => `Se eliminó ${nameOf(id)}.`);
  const deleteEdge = useNetworkMutation(api.deleteEdge, (id) => {
    const edge = network.edges.find((e) => e.id === id);
    return `Se eliminó la conexión ${edge ? edgeLabel(edge) : id}.`;
  });

  const nodeId = network.nodes.find((n) => n.id === nodeChoice)?.id ?? network.nodes[0]?.id ?? "";
  const edge = network.edges.find((e) => e.id === edgeChoice) ?? network.edges[0];
  const inUse = network.edges.filter((e) => e.source === nodeId || e.target === nodeId);
  const busy = deleteNode.isPending || deleteEdge.isPending;
  const error = deleteNode.error ?? deleteEdge.error;

  return (
    <div className="grid gap-6">
      <section className="grid gap-3" aria-labelledby="delete-node-title">
        <h3 id="delete-node-title" className="text-sm font-medium">
          Eliminar una base o zona
        </h3>
        <SelectField
          id="delete-node"
          label="Lugar"
          value={nodeId}
          onValueChange={setNodeChoice}
          options={nodeOptions(network.nodes)}
          placeholder="No hay lugares"
        />
        {inUse.length > 0 && (
          <p id="delete-node-hint" className="text-xs text-muted-foreground">
            Antes elimine {inUse.length === 1 ? "su conexión" : `sus ${inUse.length} conexiones`}:{" "}
            {joinList(inUse.map(edgeLabel))}.
          </p>
        )}
        <ConfirmDelete
          label="Eliminar lugar"
          title={`¿Eliminar ${nameOf(nodeId)}?`}
          description="Se borra junto con sus técnicos. Esta acción no se puede deshacer."
          disabled={!nodeId || busy || inUse.length > 0}
          onConfirm={() => {
            deleteEdge.reset();
            deleteNode.mutate(nodeId);
          }}
        />
      </section>
      <section className="grid gap-3" aria-labelledby="delete-edge-title">
        <h3 id="delete-edge-title" className="text-sm font-medium">
          Eliminar una conexión
        </h3>
        <SelectField
          id="delete-edge"
          label="Conexión"
          value={edge?.id ?? ""}
          onValueChange={setEdgeChoice}
          options={network.edges.map((e) => ({ value: e.id, label: edgeLabel(e) }))}
          placeholder="No hay conexiones"
        />
        <ConfirmDelete
          label="Eliminar conexión"
          title={edge ? `¿Eliminar ${edgeLabel(edge)}?` : "¿Eliminar la conexión?"}
          description="El trayecto deja de contar para la cobertura. Esta acción no se puede deshacer."
          disabled={!edge || busy}
          onConfirm={() => {
            if (!edge) return;
            deleteNode.reset();
            deleteEdge.mutate(edge.id);
          }}
        />
      </section>
      <FormError id="delete-error" message={error ? describeError(error) : null} />
    </div>
  );
}
