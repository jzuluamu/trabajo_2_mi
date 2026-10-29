import { AlertTriangle, RotateCcw, type LucideIcon } from "lucide-react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed bg-card px-6 py-14 text-center">
      <span className="grid size-11 place-items-center rounded-full bg-secondary text-primary">
        <Icon className="size-5" aria-hidden />
      </span>
      <div className="space-y-1">
        <h3 className="font-medium">{title}</h3>
        <p className="max-w-prose text-sm text-pretty text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div
      role="alert"
      className="flex flex-col items-center gap-3 rounded-xl border border-destructive/30 bg-card px-6 py-12 text-center"
    >
      <AlertTriangle className="size-6 text-destructive" aria-hidden />
      <p className="max-w-prose text-sm text-pretty">{message}</p>
      <Button variant="outline" size="sm" onClick={onRetry}>
        <RotateCcw />
        Reintentar
      </Button>
    </div>
  );
}

export function NetworkSkeleton() {
  return (
    <div className="space-y-6" aria-busy="true" aria-label="Cargando la red">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {Array.from({ length: 4 }, (_, index) => (
          <Skeleton key={index} className="h-24 rounded-xl" />
        ))}
      </div>
      <Skeleton className="h-105 rounded-xl sm:h-130 xl:h-150" />
    </div>
  );
}
