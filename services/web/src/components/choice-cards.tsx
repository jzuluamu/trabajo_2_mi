import type { LucideIcon } from "lucide-react";

import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { cn } from "@/lib/utils";

export interface Choice<T extends string> {
  value: T;
  label: string;
  description: string;
  icon: LucideIcon;
}

interface ChoiceCardsProps<T extends string> {
  id: string;
  legend: string;
  value: T;
  onValueChange: (value: T) => void;
  choices: readonly Choice<T>[];
}

/** Elección entre pocas opciones con una frase que explica cada una (radios accesibles). */
export function ChoiceCards<T extends string>({
  id,
  legend,
  value,
  onValueChange,
  choices,
}: ChoiceCardsProps<T>) {
  return (
    <fieldset className="grid gap-2">
      <legend className="mb-2 text-sm font-medium">{legend}</legend>
      <RadioGroup
        value={value}
        onValueChange={(next) => {
          onValueChange(next as T);
        }}
        className="grid gap-2 sm:grid-cols-2"
      >
        {choices.map((choice) => {
          const itemId = `${id}-${choice.value}`;
          const Icon = choice.icon;
          return (
            <Label
              key={choice.value}
              htmlFor={itemId}
              className={cn(
                "flex cursor-pointer items-start gap-3 rounded-lg border bg-card p-3 font-normal transition-colors hover:bg-accent",
                "has-[[data-state=checked]]:border-foreground has-[[data-state=checked]]:bg-accent",
              )}
            >
              <RadioGroupItem id={itemId} value={choice.value} className="mt-0.5" />
              <span className="grid gap-0.5">
                <span className="flex items-center gap-1.5 text-sm font-medium">
                  <Icon className="size-4 text-muted-foreground" aria-hidden />
                  {choice.label}
                </span>
                <span className="text-xs text-muted-foreground">{choice.description}</span>
              </span>
            </Label>
          );
        })}
      </RadioGroup>
    </fieldset>
  );
}
