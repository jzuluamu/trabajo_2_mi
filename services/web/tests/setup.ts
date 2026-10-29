import "@testing-library/jest-dom/vitest";

import type { CytoscapeOptions } from "cytoscape";

// jsdom no implementa canvas: Cytoscape corre en modo headless (mismo modelo de grafo, sin dibujo).
// La última instancia queda en `lastCy()` para simular clics en nodos desde las pruebas.
vi.mock("cytoscape", async (importOriginal) => {
  const actual = await importOriginal<{ default: typeof import("cytoscape") }>();
  const real = actual.default;
  const wrapped = Object.assign((options: CytoscapeOptions = {}) => {
    const cy = real({ ...options, headless: true });
    (globalThis as { __cy?: unknown }).__cy = cy;
    return cy;
  }, real);
  return { ...actual, default: wrapped };
});

if (typeof window !== "undefined") {
  // Radix (Select, Tooltip) usa APIs de puntero y de diseño que jsdom no trae.
  class ResizeObserverStub {
    observe(): void {}
    unobserve(): void {}
    disconnect(): void {}
  }
  const stubs: [object, string, unknown][] = [
    [window, "ResizeObserver", ResizeObserverStub],
    [Element.prototype, "scrollIntoView", () => undefined],
    [Element.prototype, "hasPointerCapture", () => false],
    [Element.prototype, "releasePointerCapture", () => undefined],
  ];
  for (const [target, name, value] of stubs) {
    if (!(name in target)) Object.defineProperty(target, name, { value, configurable: true });
  }
}
