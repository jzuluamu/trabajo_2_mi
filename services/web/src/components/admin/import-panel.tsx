import { FileJson, Loader2, RefreshCcw, SquarePlus, Upload } from "lucide-react";
import { useState, type DragEvent, type SubmitEvent } from "react";

import { ChoiceCards } from "@/components/choice-cards";
import { FormError } from "@/components/form-fields";
import { Button } from "@/components/ui/button";
import { useNetworkMutation } from "@/hooks/use-network";
import { api } from "@/lib/api";
import { describeError, FormInputError, parseNetworkFile } from "@/lib/network-format";
import type { ImportPayload } from "@/lib/types";
import { cn } from "@/lib/utils";

type Mode = "replace" | "add";

const MODES = [
  {
    value: "replace",
    label: "Reemplazar todo",
    description: "Se borra la red actual y queda solo lo del archivo.",
    icon: RefreshCcw,
  },
  {
    value: "add",
    label: "Agregar",
    description: "Se suma lo del archivo a la red actual.",
    icon: SquarePlus,
  },
] as const;

export function ImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [mode, setMode] = useState<Mode>("replace");
  const [localError, setLocalError] = useState<string | null>(null);
  const load = useNetworkMutation(
    (payload: ImportPayload) => api.importNetwork(payload),
    (payload) =>
      `Red cargada: ${payload.nodes.length} lugares y ${payload.edges.length} conexiones.`,
  );

  const pick = (picked: File | null | undefined) => {
    setFile(picked ?? null);
    setLocalError(null);
  };

  const onDrop = (event: DragEvent<HTMLLabelElement>) => {
    event.preventDefault();
    setDragging(false);
    pick(event.dataTransfer.files[0]);
  };

  const submit = async (event: SubmitEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    if (!file) {
      setLocalError("Elija un archivo para cargar.");
      return;
    }
    try {
      load.mutate(parseNetworkFile(await file.text(), mode === "replace"));
    } catch (error) {
      if (!(error instanceof FormInputError)) throw error;
      setLocalError(error.message);
    }
  };

  const error = localError ?? (load.error ? describeError(load.error) : null);
  return (
    <form className="grid gap-5" onSubmit={(event) => void submit(event)} noValidate>
      <label
        htmlFor="import-file"
        onDragOver={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => {
          setDragging(false);
        }}
        onDrop={onDrop}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-2 rounded-lg border border-dashed bg-muted/40 px-4 py-8 text-center transition-colors hover:bg-muted",
          "has-[:focus-visible]:ring-[3px] has-[:focus-visible]:ring-ring/50",
          dragging && "border-foreground bg-muted",
        )}
      >
        {file ? (
          <FileJson className="size-6 text-foreground" aria-hidden />
        ) : (
          <Upload className="size-6 text-muted-foreground" aria-hidden />
        )}
        <span className="text-sm font-medium">
          {file ? file.name : "Arrastre el archivo aquí o haga clic para elegirlo"}
        </span>
        <span className="text-xs text-muted-foreground">
          Un archivo .json con la red, por ejemplo <code className="font-mono">red_demo.json</code>
        </span>
        <input
          id="import-file"
          type="file"
          accept=".json,application/json"
          className="sr-only"
          aria-label="Archivo de la red"
          onChange={(event) => {
            pick(event.target.files?.[0]);
          }}
        />
      </label>
      <ChoiceCards
        id="import-mode"
        legend="¿Qué hacer con la red actual?"
        value={mode}
        onValueChange={setMode}
        choices={MODES}
      />
      <Button type="submit" disabled={load.isPending}>
        {load.isPending ? <Loader2 className="animate-spin" aria-hidden /> : <Upload aria-hidden />}
        Cargar red
      </Button>
      <FormError id="import-error" message={error} />
    </form>
  );
}
