import { vitePreprocess } from "@sveltejs/vite-plugin-svelte";
import removeConsole from "vite-plugin-svelte-console-remover";
import path from "path";
import adapter from "@sveltejs/adapter-static";

// Get environment variables for assets configuration
const ASSETS_BASE_URL =
  process.env.VITE_ASSETS_BASE_URL ||
  (process.env.NODE_ENV === "production"
    ? process.env.VITE_BASE_URL_PROD
    : process.env.VITE_BASE_URL_DEV);

console.log("VITE_ASSETS_BASE_URL:", ASSETS_BASE_URL);
console.log("VITE_BASE_PATH:", (process.env.VITE_BASE_PATH || "").trim());

/** @type {import('@sveltejs/kit').Config} */
const config = {
  // Consult https://kit.svelte.dev/docs/integrations#preprocessors
  // for more information about preprocessors
  preprocess: vitePreprocess(),

  kit: {
    paths: {
      relative: false,
      base: (process.env.VITE_BASE_PATH || "").trim(),
      assets: ASSETS_BASE_URL,
    },
    // adapter-auto only supports some environments, see https://kit.svelte.dev/docs/adapter-auto for a list.
    // If your environment is not supported, or you settled on a specific environment, switch out the adapter.
    // See https://kit.svelte.dev/docs/adapters for more information about adapters.
    adapter: adapter({
      pages: "build",
      assets: "build",
      fallback: "index.html",
      precompress: false,
      strict: true,
      vite: {
        plugins: [removeConsole()],
      },
    }),
    appDir: "_app",
    alias: {
      $components: path.resolve("./src/components"),
      $lib: path.resolve("./src/lib"),
      $pages: path.resolve("./src/pages"),
      img: path.resolve("./static/img"), // Adding alias for img to point to static/img
    },
    csrf: {
      checkOrigin: process.env.NODE_ENV === "production",
    },
    files: {
      assets: "static", // This tells SvelteKit where to look for static assets
    },
  },
};

export default config;
