/// <reference types="vitest/config" />
import { fileURLToPath } from "node:url";

import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const src = fileURLToPath(new URL("./src", import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": src } },
  build: {
    outDir: "dist/client",
    emptyOutDir: true,
    sourcemap: false,
    rolldownOptions: {
      output: {
        // Librerías en chunks propios: cambian poco y el navegador las conserva en caché.
        codeSplitting: {
          groups: [
            { name: "cytoscape", test: /node_modules[\\/]cytoscape/ },
            { name: "react", test: /node_modules[\\/](react|react-dom|scheduler)[\\/]/ },
            { name: "vendor", test: /node_modules/ },
          ],
        },
      },
    },
  },
  // En desarrollo (`npm run dev`), el BFF corre aparte (`npm run dev:server`) en :8080.
  server: { proxy: { "/bff": "http://localhost:8080" } },
  test: {
    globals: true,
    restoreMocks: true,
    setupFiles: ["./tests/setup.ts"],
    projects: [
      {
        extends: true,
        test: { name: "server", environment: "node", include: ["tests/server/**/*.test.ts"] },
      },
      {
        extends: true,
        test: {
          name: "ui",
          environment: "jsdom",
          include: ["tests/lib/**/*.test.ts", "tests/ui/**/*.test.tsx"],
        },
      },
    ],
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}", "server/**/*.ts"],
      // Puntos de entrada sin lógica (como app.py en la consola Streamlit).
      exclude: ["src/main.tsx", "server/index.ts", "src/vite-env.d.ts"],
      reporter: ["text"],
      thresholds: { lines: 85, functions: 85, branches: 85, statements: 85 },
    },
  },
});
