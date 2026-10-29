import { ArrowLeft, ArrowLeftRight, ArrowRight, TriangleAlert } from "lucide-react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMinutes, type NodeCardData, type NodeLink } from "@/lib/network-format";

const SENSE: Record<NodeLink["arrow"], { icon: typeof ArrowRight; text: string }> = {
  "↔": { icon: ArrowLeftRight, text: "ida y vuelta" },
  "→": { icon: ArrowRight, text: "solo ida (hacia allá)" },
  "←": { icon: ArrowLeft, text: "solo llegada (desde allá)" },
};

export function NodeCard({ card }: { card: NodeCardData }) {
  return (
    <Card className="gap-4" aria-live="polite">
      <CardHeader>
        <CardTitle className="flex items-center justify-between gap-2 text-base">
          <h3>{card.name}</h3>
          <Badge variant="secondary">{card.typeLabel}</Badge>
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Identificador <span className="font-mono">{card.id}</span>
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {card.note && (
          <Alert variant="warning">
            <TriangleAlert aria-hidden />
            <AlertDescription>{card.note}</AlertDescription>
          </Alert>
        )}
        {card.isBase && (
          <section className="space-y-2">
            <h4 className="text-sm font-medium">Técnicos ({card.technicians.length})</h4>
            {card.technicians.length ? (
              <ul className="divide-y rounded-lg border">
                {card.technicians.map((technician) => (
                  <li
                    key={technician.id}
                    className="flex items-center justify-between gap-2 px-3 py-2 text-sm"
                  >
                    <span className="min-w-0 truncate">
                      {technician.name}{" "}
                      <span className="font-mono text-xs text-muted-foreground">
                        {technician.id}
                      </span>
                    </span>
                    <Badge variant={technician.available ? "success" : "secondary"}>
                      {technician.available ? "Disponible" : "No disponible"}
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">Sin técnicos registrados.</p>
            )}
          </section>
        )}
        <section className="space-y-2">
          <h4 className="text-sm font-medium">Trayectos ({card.links.length})</h4>
          {card.links.length > 0 && (
            <ul className="divide-y rounded-lg border" aria-label={`Trayectos de ${card.name}`}>
              {card.links.map((link) => {
                const { icon: Icon, text } = SENSE[link.arrow];
                return (
                  <li key={link.edgeId} className="flex items-center gap-3 px-3 py-2 text-sm">
                    <Icon className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate">{link.other}</span>
                      <span className="block text-xs text-muted-foreground">{text}</span>
                    </span>
                    <span className="tabular-nums">{formatMinutes(link.minutes)}</span>
                  </li>
                );
              })}
            </ul>
          )}
        </section>
      </CardContent>
    </Card>
  );
}
