import cytoscape, {
  type Core,
  type EdgeSingular,
  type NodeSingular,
  type Position,
} from "cytoscape";
import { Maximize, Shuffle, ZoomIn, ZoomOut, type LucideIcon } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useGraphPalette } from "@/hooks/use-theme";
import type { CoverageOverlay } from "@/lib/coverage-format";
import {
  buildElements,
  DRAFT_ID,
  draftElement,
  graphStyle,
  graphSummary,
  idealEdgeLength,
  OVERLAY_CLASSES,
  overlayFor,
  type DraftEdge,
} from "@/lib/graph-elements";
import type { Network } from "@/lib/types";
import { cn } from "@/lib/utils";

const PADDING = 56;

/**
 * Posiciones compartidas por todos los mapas de la sesión: un nodo arrastrado en «Red» aparece
 * en el mismo lugar en «Cobertura» y «Configurar red», y recargar la red no reordena nada.
 */
const sharedPositions = new Map<string, Position>();

const prefersReducedMotion = (): boolean =>
  typeof window.matchMedia === "function" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

function runLayout(cy: Core, animate: boolean): void {
  cy.layout({
    name: "cose",
    randomize: false,
    animate,
    animationDuration: 300,
    fit: true,
    padding: PADDING,
    // Ajustado mirando la red demo en el navegador: sin etiquetas encimadas y con la longitud de
    // cada arista todavía proporcional a sus minutos.
    nodeDimensionsIncludeLabels: true,
    nodeRepulsion: () => 150_000,
    nodeOverlap: 20,
    edgeElasticity: () => 60,
    idealEdgeLength: (edge) => idealEdgeLength(Number(edge.data("weight"))),
    gravity: 0.6,
    componentSpacing: 60,
    numIter: 2500,
  }).run();
}

type Control = "zoom-in" | "zoom-out" | "fit" | "layout";

const CONTROLS: readonly [Control, string, LucideIcon][] = [
  ["zoom-in", "Acercar", ZoomIn],
  ["zoom-out", "Alejar", ZoomOut],
  ["fit", "Ajustar a la vista", Maximize],
  ["layout", "Reorganizar", Shuffle],
];

interface HoverInfo {
  text: string;
  x: number;
  y: number;
}

export interface NetworkGraphProps {
  network: Network;
  selected?: string | null;
  onSelect?: (nodeId: string | null) => void;
  coverage?: CoverageOverlay | null;
  draft?: DraftEdge | null;
  label?: string;
  className?: string;
}

/**
 * Mapa interactivo de la red: arrastrar, zoom, hover con resumen y clic para elegir un nodo.
 * Cytoscape dibuja en un canvas y muestra los nombres como texto plano: los datos de la API no
 * se interpretan como HTML. Las posiciones se conservan al recargar la red y entre pestañas.
 */
export function NetworkGraph({
  network,
  selected = null,
  onSelect,
  coverage = null,
  draft = null,
  label,
  className,
}: NetworkGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);
  const onSelectRef = useRef(onSelect);
  const palette = useGraphPalette();
  const paletteRef = useRef(palette);
  const [hover, setHover] = useState<HoverInfo | null>(null);

  useEffect(() => {
    onSelectRef.current = onSelect;
  }, [onSelect]);

  useEffect(() => {
    paletteRef.current = palette;
    cyRef.current?.style(graphStyle(palette));
  }, [palette]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const known = sharedPositions;
    const cy = cytoscape({
      container,
      elements: buildElements(network),
      style: graphStyle(paletteRef.current),
      layout: { name: "preset" },
      minZoom: 0.3,
      maxZoom: 2.5,
      boxSelectionEnabled: false,
      autounselectify: true,
    });
    cy.nodes().forEach((node) => {
      const position = known.get(node.id());
      if (position) node.position(position);
    });
    const missing = cy
      .nodes()
      .toArray()
      .some((node) => !known.has(node.id()));
    const remember = () => {
      cy.nodes().forEach((node) => {
        known.set(node.id(), { ...node.position() });
      });
    };
    cy.on("layoutstop dragfree", remember);
    if (missing) runLayout(cy, false);
    else cy.fit(undefined, PADDING);

    cy.on("tap", "node", (event) => {
      onSelectRef.current?.((event.target as NodeSingular).id());
    });
    cy.on("tap", (event) => {
      const target: unknown = event.target;
      if (target === cy) onSelectRef.current?.(null);
    });
    cy.on("mouseover", "node, edge", (event) => {
      const { x, y } = event.renderedPosition;
      const target = event.target as NodeSingular | EdgeSingular;
      setHover({ text: String(target.data("tooltip")), x, y });
    });
    cy.on("mouseout viewport", () => {
      setHover(null);
    });
    cyRef.current = cy;
    return () => {
      remember();
      cy.destroy();
      cyRef.current = null;
    };
  }, [network]);

  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;
    const overlay = overlayFor(network, { selected, coverage });
    const element = draftElement(network, draft);
    cy.batch(() => {
      cy.remove(cy.getElementById(DRAFT_ID));
      if (element) cy.add(element);
      cy.elements().removeClass([...OVERLAY_CLASSES]);
      cy.nodes().forEach((node) => {
        node.data("label", overlay.labels.get(node.id()) ?? node.data("baseLabel"));
      });
      for (const [id, classes] of overlay.classes) cy.getElementById(id).addClass(classes);
    });
  }, [network, selected, coverage, draft]);

  const handleControl = (control: Control) => {
    const cy = cyRef.current;
    if (!cy) return;
    if (control === "fit") {
      cy.fit(undefined, PADDING);
    } else if (control === "layout") {
      runLayout(cy, !prefersReducedMotion());
    } else {
      cy.zoom({
        level: cy.zoom() * (control === "zoom-in" ? 1.25 : 0.8),
        renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
      });
    }
  };

  return (
    <div
      className={cn("relative h-105 w-full overflow-hidden sm:h-130 xl:h-150", className)}
      style={{ backgroundColor: palette.canvas }}
    >
      <div
        ref={containerRef}
        role="img"
        aria-label={label ?? graphSummary(network)}
        // Tamaño explícito: Cytoscape fuerza `position: relative` en su contenedor, así que
        // `absolute inset-0` lo dejaría con altura 0 y el mapa no se vería.
        className="size-full"
        data-testid="network-graph"
      />
      {network.nodes.length === 0 && (
        <p className="absolute inset-0 grid place-items-center px-6 text-center text-sm text-muted-foreground">
          Aún no hay nodos para dibujar.
        </p>
      )}
      <div
        role="toolbar"
        aria-label="Controles del mapa"
        className="absolute top-3 right-3 flex gap-1 rounded-lg border bg-card/90 p-1 shadow-sm backdrop-blur sm:flex-col"
      >
        {CONTROLS.map(([control, name, Icon]) => (
          <Tooltip key={name}>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-11 sm:size-9"
                aria-label={name}
                onClick={() => {
                  handleControl(control);
                }}
              >
                <Icon />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">{name}</TooltipContent>
          </Tooltip>
        ))}
      </div>
      {hover && (
        <div
          role="tooltip"
          className="pointer-events-none absolute z-10 max-w-64 -translate-x-1/2 -translate-y-[calc(100%+14px)] rounded-md border bg-popover px-2.5 py-1.5 text-xs text-popover-foreground shadow-md"
          style={{ left: hover.x, top: hover.y }}
        >
          {hover.text}
        </div>
      )}
    </div>
  );
}
