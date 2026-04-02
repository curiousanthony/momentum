import { defineConfig } from "vite";

/** Where aggregator output + runtime API live during local dev (see README / scripts/dev-server.sh). */
const runtimeDevTarget =
  process.env.MOMENTUM_RUNTIME_URL?.replace(/\/$/, "") ?? "http://127.0.0.1:7420";

export default defineConfig({
  base: "./",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // Real data + settings API are served by aggregator.runtime from ~/.cursor/dashboard (or RUNTIME_DIR).
      "/state.json": { target: runtimeDevTarget, changeOrigin: true },
      "/api": { target: runtimeDevTarget, changeOrigin: true },
    },
  },
});
