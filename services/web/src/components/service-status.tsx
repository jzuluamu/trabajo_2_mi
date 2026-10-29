import { CircleCheck, CircleX } from "lucide-react";

import { Skeleton } from "@/components/ui/skeleton";
import { useHealth } from "@/hooks/use-network";
import { cn } from "@/lib/utils";

/** Nombres para el usuario; el nombre técnico queda en el `title`. */
const SERVICE_LABELS: Record<string, string> = {
  "network-service": "Red",
  "routing-service": "Consultas",
};
const SERVICES = Object.keys(SERVICE_LABELS);

/** Estado del sistema (`/health`, público). Icono + texto: no depende solo del color. */
export function ServiceStatus({ className }: { className?: string }) {
  const health = useHealth();
  if (health.isPending) {
    return (
      <Skeleton
        className={cn("h-7 w-32 rounded-full", className)}
        aria-label="Consultando el sistema"
      />
    );
  }
  const services =
    health.data?.services ?? SERVICES.map((name) => ({ name, status: "down" as const }));
  const down = services.filter((service) => service.status !== "ok");
  const details = services.map(
    (s) => `${s.name}: ${s.status === "ok" ? "operativo" : "no disponible"}`,
  );
  return (
    <ul
      role="status"
      aria-label="Estado del sistema"
      title={details.join(" · ")}
      className={cn("flex flex-wrap gap-2", className)}
    >
      {down.length === 0 ? (
        <li className="flex items-center gap-1.5 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground">
          <CircleCheck className="size-3.5 text-success" aria-hidden />
          Todo en línea
        </li>
      ) : (
        down.map((service) => (
          <li
            key={service.name}
            className="flex items-center gap-1.5 rounded-full border border-destructive/30 bg-card px-3 py-1 text-xs text-destructive"
          >
            <CircleX className="size-3.5" aria-hidden />
            {SERVICE_LABELS[service.name] ?? service.name}: sin conexión
          </li>
        ))
      )}
    </ul>
  );
}
