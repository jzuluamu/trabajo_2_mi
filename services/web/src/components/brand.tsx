import { cn } from "@/lib/utils";

/**
 * Logotipo: un pin de ubicación con tres nodos conectados (la red de bases y zonas).
 * El nodo de color es la base de origen. `inverted` es para fondos oscuros (encabezado y
 * panel de marca en azul noche).
 */
export function BrandMark({
  inverted = false,
  className,
}: {
  inverted?: boolean;
  className?: string;
}) {
  const tile = inverted ? "fill-ink-foreground" : "fill-ink";
  const line = inverted ? "stroke-ink" : "stroke-ink-foreground";
  const node = inverted ? "fill-ink" : "fill-ink-foreground";
  return (
    <svg viewBox="0 0 32 32" className={cn("size-9 shrink-0", className)} aria-hidden>
      <rect width="32" height="32" rx="9" className={tile} />
      <path
        d="M16 5.5c-4.6 0-8.2 3.5-8.2 8 0 5.8 8.2 13 8.2 13s8.2-7.2 8.2-13c0-4.5-3.6-8-8.2-8z"
        fill="none"
        strokeWidth="1.7"
        strokeLinejoin="round"
        className={line}
      />
      <path
        d="M12.6 12.2 19.4 11.4 16 17"
        fill="none"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeLinejoin="round"
        className={line}
      />
      <circle cx="12.6" cy="12.2" r="1.9" className="fill-brand" />
      <circle cx="19.4" cy="11.4" r="1.9" className={node} />
      <circle cx="16" cy="17" r="1.9" className={node} />
    </svg>
  );
}

export function Brand({ inverted = false, className }: { inverted?: boolean; className?: string }) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <BrandMark inverted={inverted} />
      <span className="leading-tight">
        <span
          className={cn(
            "block text-base font-bold tracking-tight",
            inverted ? "text-ink-foreground" : "text-ink dark:text-foreground",
          )}
        >
          ServicioCerca
        </span>
        <span
          className={cn("block text-xs", inverted ? "text-ink-muted" : "text-muted-foreground")}
        >
          Consola de operación
        </span>
      </span>
    </span>
  );
}
