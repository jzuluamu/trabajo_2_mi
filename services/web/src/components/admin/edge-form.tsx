import { ArrowLeftRight, ArrowRight, Loader2 } from "lucide-react";
import { useEffect, useState, type SubmitEvent } from "react";

import { ChoiceCards } from "@/components/choice-cards";
import { Field, FormError, SelectField } from "@/components/form-fields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useNetworkMutation } from "@/hooks/use-network";
import { api } from "@/lib/api";
import type { DraftEdge } from "@/lib/graph-elements";
import {
  describeError,
  edgePayload,
  formatMinutes,
  nextId,
  nodeOptions,
  WEIGHT_MAX_MINUTES,
  weightInRange,
} from "@/lib/network-format";
import type { Network } from "@/lib/types";

type Direction = "both" | "one";

const DIRECTIONS = [
  {
    value: "both",
    label: "Ida y vuelta",
    description: "Se puede ir y volver por este trayecto.",
    icon: ArrowLeftRight,
  },
  {
    value: "one",
    label: "Solo ida",
    description: "Solo se recorre desde el primer lugar hacia el segundo.",
    icon: ArrowRight,
  },
] as const;

interface EdgeFormProps {
  network: Network;
  onDraftChange: (draft: DraftEdge | null) => void;
}

/** Nueva conexión: lo que se escribe se dibuja en el mapa antes de guardarlo. */
export function EdgeForm({ network, onDraftChange }: EdgeFormProps) {
  const ids = network.nodes.map((node) => node.id);
  const [customId, setCustomId] = useState<string | null>(null);
  const [source, setSource] = useState(ids[0] ?? "");
  const [target, setTarget] = useState(ids[1] ?? ids[0] ?? "");
  const [minutes, setMinutes] = useState("10");
  const [direction, setDirection] = useState<Direction>("both");
  const [localError, setLocalError] = useState<string | null>(null);
  const names = new Map(network.nodes.map((node) => [node.id, node.name]));
  const create = useNetworkMutation(
    api.createEdge,
    (edge) =>
      `Listo: se conectó ${names.get(edge.source) ?? edge.source} con ${names.get(edge.target) ?? edge.target} (${formatMinutes(edge.weight)}).`,
  );

  const edgeId =
    customId ??
    nextId(
      "E",
      network.edges.map((edge) => edge.id),
    );
  const weight = minutes.trim() === "" ? Number.NaN : Number(minutes);
  const inRange = weightInRange(weight);
  const bidirectional = direction === "both";

  useEffect(() => {
    onDraftChange(
      source && target && source !== target && Number.isFinite(weight)
        ? { source, target, weight, bidirectional, valid: inRange }
        : null,
    );
  }, [source, target, weight, bidirectional, inRange, onDraftChange]);

  useEffect(
    () => () => {
      onDraftChange(null);
    },
    [onDraftChange],
  );

  const submit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    if (ids.length < 2) {
      setLocalError("Primero agregue al menos dos lugares (bases o zonas).");
      return;
    }
    if (source === target) {
      setLocalError("Elija dos lugares distintos.");
      return;
    }
    if (!Number.isFinite(weight)) {
      setLocalError("Escriba cuántos minutos toma el trayecto.");
      return;
    }
    // Un peso fuera de rango se envía igual: network-service responde INVALID_WEIGHT (contrato).
    create.mutate(edgePayload(edgeId, source, target, weight, bidirectional), {
      onSuccess: () => {
        setCustomId(null);
      },
    });
  };

  const options = nodeOptions(network.nodes);
  const error = localError ?? (create.error ? describeError(create.error) : null);
  return (
    <form className="grid gap-5" onSubmit={submit} noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <SelectField
          id="edge-source"
          label="Desde"
          value={source}
          onValueChange={setSource}
          options={options}
        />
        <SelectField
          id="edge-target"
          label="Hasta"
          value={target}
          onValueChange={setTarget}
          options={options}
        />
      </div>
      <Field
        id="edge-weight"
        label="¿Cuántos minutos toma el trayecto?"
        hint={
          inRange || !Number.isFinite(weight) ? undefined : (
            <span className="text-warning">
              Debe ser mayor que 0 y como máximo {WEIGHT_MAX_MINUTES} minutos (24 horas).
            </span>
          )
        }
      >
        <div className="relative">
          <Input
            id="edge-weight"
            type="number"
            inputMode="decimal"
            step={1}
            className="pr-14 tabular-nums"
            value={minutes}
            aria-describedby={inRange ? undefined : "edge-weight-hint"}
            aria-invalid={Number.isFinite(weight) && !inRange ? true : undefined}
            onChange={(event) => {
              setMinutes(event.target.value);
            }}
          />
          <span
            className="pointer-events-none absolute top-1/2 right-3 -translate-y-1/2 text-sm text-muted-foreground"
            aria-hidden
          >
            min
          </span>
        </div>
      </Field>
      <ChoiceCards
        id="edge-direction"
        legend="Sentido"
        value={direction}
        onValueChange={setDirection}
        choices={DIRECTIONS}
      />
      <Field id="edge-id" label="Identificador" hint="Se propone el siguiente libre.">
        <Input
          id="edge-id"
          className="font-mono"
          aria-describedby="edge-id-hint"
          value={edgeId}
          onChange={(event) => {
            setCustomId(event.target.value.toUpperCase());
          }}
        />
      </Field>
      <Button type="submit" disabled={create.isPending}>
        {create.isPending && <Loader2 className="animate-spin" aria-hidden />}
        Guardar conexión
      </Button>
      <FormError id="edge-error" message={error} />
    </form>
  );
}
