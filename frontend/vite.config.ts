import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";
import { resolve } from "path";
import { staticAssetsPlugin } from "./src/lib/vite-plugins/static-assets";
import type { Plugin } from "vite";

// Virtual module plugin for EE plugin stub in OSS builds
function eePluginStub(): Plugin {
  const virtualModuleId = "virtual:ee-plugin";
  const resolvedVirtualModuleId = "\0" + virtualModuleId;

  return {
    name: "ee-plugin-stub",
    resolveId(id) {
      if (id === virtualModuleId) {
        return resolvedVirtualModuleId;
      }
    },
    load(id) {
      if (id === resolvedVirtualModuleId) {
        // Return a stub that throws an error when called
        // This will be caught by the try/catch in +layout.svelte
        return `
          export function registerEE() {
            throw new Error("EE plugin not available in OSS build");
          }
          export const isEE = false;
        `;
      }
    },
  };
}

export default defineConfig({
  plugins: [
    sveltekit(),
    staticAssetsPlugin(), // Add our custom plugin for handling static assets
    eePluginStub(), // Provide stub for EE plugin in OSS builds
  ],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"],
  },
  build: {
    sourcemap: process.env.NODE_ENV !== "production",
  },
  server: {
    fs: {
      // Allow serving files from the static directory
      allow: [resolve("./static")],
    },
    // Allow cookies to be sent cross-origin
    cors: {
      origin: "http://localhost:8000", // Django development server
      credentials: true,
      exposedHeaders: ["Content-Type", "X-CSRFToken"],
    },
    proxy: {
      // Proxy API requests to Django server
      "/_holly/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
        secure: false,
        cookieDomainRewrite: "localhost",
        withCredentials: true,
      },
    },
    // Add HTTPS options if needed for local development
    // https: {
    //   key: fs.readFileSync('/path/to/server.key'),
    //   cert: fs.readFileSync('/path/to/server.cert'),
    // },
  },
});
