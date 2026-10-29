import { Building2, Loader2, MapPin, Plus, Trash2 } from "lucide-react";
import { useState, type SubmitEvent } from "react";

import { ChoiceCards } from "@/components/choice-cards";
import { Field, FormError } from "@/components/form-fields";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { useNetworkMutation } from "@/hooks/use-network";
import { api } from "@/lib/api";
import {
  describeError,
  FormInputError,
  nodePayload,
  suggestNodeId,
  type TechnicianDraft,
} from "@/lib/network-format";
import type { Network, NodeType } from "@/lib/types";

const TYPES = [
  {
    value: "BASE",
    label: "Base",
    description: "Sede desde donde salen los técnicos.",
    icon: Building2,
  },
  {
    value: "ZONE",
    label: "Zona",
    description: "Lugar donde se atienden solicitudes.",
    icon: MapPin,
  },
] as const;

const EMPTY_TECHNICIAN: TechnicianDraft = { name: "", available: true };

export function NodeForm({ network }: { network: Network }) {
  const [type, setType] = useState<NodeType>("BASE");
  const [name, setName] = useState("");
  const [customId, setCustomId] = useState<string | null>(null);
  const [technicians, setTechnicians] = useState<TechnicianDraft[]>([EMPTY_TECHNICIAN]);
  const [localError, setLocalError] = useState<string | null>(null);
  const create = useNetworkMutation(api.createNode, (node) => `Listo: se agregó ${node.name}.`);

  const takenIds = network.nodes.map((node) => node.id);
  const nodeId = customId ?? suggestNodeId(type, name, takenIds);

  const updateTechnician = (index: number, change: Partial<TechnicianDraft>) => {
    setTechnicians((list) => list.map((t, i) => (i === index ? { ...t, ...change } : t)));
  };

  const submit = (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    let payload;
    try {
      const takenTechnicians = network.nodes.flatMap((node) => node.technicians.map((t) => t.id));
      payload = nodePayload(nodeId, type, name, technicians, takenTechnicians);
    } catch (error) {
      if (!(error instanceof FormInputError)) throw error;
      setLocalError(error.message);
      return;
    }
    create.mutate(payload, {
      onSuccess: () => {
        setName("");
        setCustomId(null);
        setTechnicians([EMPTY_TECHNICIAN]);
      },
    });
  };

  const error = localError ?? (create.error ? describeError(create.error) : null);
  return (
    <form className="grid gap-5" onSubmit={submit} noValidate>
      <ChoiceCards
        id="node-type"
        legend="¿Qué quiere agregar?"
        value={type}
        onValueChange={setType}
        choices={TYPES}
      />
      <Field id="node-name" label="Nombre">
        <Input
          id="node-name"
          placeholder={type === "BASE" ? "Ej.: Base Este" : "Ej.: Las Palmas"}
          autoComplete="off"
          value={name}
          onChange={(event) => {
            setName(event.target.value);
          }}
        />
      </Field>
      <Field
        id="node-id"
        label="Identificador"
        hint="Se propone a partir del nombre. Puede cambiarlo si lo necesita."
      >
        <Input
          id="node-id"
          className="font-mono"
          aria-describedby="node-id-hint"
          placeholder={type === "BASE" ? "B_ESTE" : "Z_LAS_PALMAS"}
          value={nodeId}
          onChange={(event) => {
            setCustomId(event.target.value.toUpperCase());
          }}
        />
      </Field>
      {type === "BASE" && (
        <fieldset className="grid gap-2">
          <legend className="mb-1 text-sm font-medium">Técnicos de la base</legend>
          <ul className="grid gap-2">
            {technicians.map((technician, index) => {
              const number = index + 1;
              return (
                <li key={index} className="flex items-center gap-2">
                  <Label htmlFor={`technician-${number}`} className="sr-only">
                    Nombre del técnico {number}
                  </Label>
                  <Input
                    id={`technician-${number}`}
                    placeholder="Nombre"
                    autoComplete="off"
                    value={technician.name}
                    onChange={(event) => {
                      updateTechnician(index, { name: event.target.value });
                    }}
                  />
                  <div className="flex shrink-0 items-center gap-2">
                    <Switch
                      id={`technician-${number}-available`}
                      checked={technician.available}
                      onCheckedChange={(available) => {
                        updateTechnician(index, { available });
                      }}
                      aria-label={`Técnico ${number} disponible`}
                    />
                    <span className="w-20 text-xs text-muted-foreground" aria-hidden>
                      {technician.available ? "Disponible" : "Ocupado"}
                    </span>
                  </div>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    className="size-11 shrink-0 sm:size-9"
                    aria-label={`Quitar técnico ${number}`}
                    disabled={technicians.length === 1}
                    onClick={() => {
                      setTechnicians((list) => list.filter((_, i) => i !== index));
                    }}
                  >
                    <Trash2 />
                  </Button>
                </li>
              );
            })}
          </ul>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="w-fit"
            onClick={() => {
              setTechnicians((list) => [...list, EMPTY_TECHNICIAN]);
            }}
          >
            <Plus aria-hidden />
            Agregar técnico
          </Button>
          <p className="text-xs text-muted-foreground">
            Las filas sin nombre no se guardan. Una base sin técnicos disponibles no puede atender.
          </p>
        </fieldset>
      )}
      <Button type="submit" disabled={create.isPending}>
        {create.isPending && <Loader2 className="animate-spin" aria-hidden />}
        {type === "BASE" ? "Agregar base" : "Agregar zona"}
      </Button>
      <FormError id="node-error" message={error} />
    </form>
  );
}
