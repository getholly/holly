import Holly from "./components/Holly.svelte"; // Ensure Holly is imported

// Initialize the Holly app
// Username and email will be primarily sourced from the Svelte store within Holly.svelte.
// Other props like csrfToken, availableLlms, repo, etc., if still needed by Holly.svelte,
// must be provided through a new mechanism (e.g., API, other stores, or direct props if static).
// For now, we pass empty/default values for props that used to come from djangoContext
// and are not part of the unified auth store.

console.log("[HOLLY-DEBUG] Initializing Holly app from holly-main.js");

const app = new Holly({
  target: document.getElementById("holly-app"),
  props: {
    // username and email props are still available in Holly.svelte,
    // but it's designed to fall back to the store. So, we can pass empty strings.
    username: "",
    email: "",
    // These props need a new source if Holly.svelte still depends on them critically.
    csrfToken: "", // Placeholder: Needs a new source if required
    availableLlms: [], // Placeholder: Needs a new source if required
    repo: "", // Placeholder
    repoUsername: "", // Placeholder
    url: "", // Placeholder
  },
});

export default app;
