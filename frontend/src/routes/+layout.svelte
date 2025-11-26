<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { routeAllowed } from "$lib/routes";
  import { page } from "$app/stores";
  import ModalLoggedOut from "$components/modals/ModalLoggedOut.svelte";
  import ModalErrorMessage from "$components/modals/ModalErrorMessage.svelte";
  import { selectedTheme } from "$lib/store/theme.store";
  import Toast from "$components/toast/Toast.svelte";
  import { base } from "$app/paths";
  // Unified auth store imports
  import { isAuthenticated, userEmail } from "$lib/store/auth/tokens.store";

  // Import Navbar component (authStore is no longer needed here as Navbar uses the unified store)
  import Navbar from "$components/navbar/Navbar.svelte"; // Adjusted path assuming Navbar.svelte is the component

  onMount(async () => {
    // The old logic to sync djangoContext to authStore is removed.
    // isAuthenticated, userEmail, etc., are now directly from the unified tokens.store.

    // Check if the route is allowed
    const route = $page.url.pathname;

    if (route !== undefined && !routeAllowed(route)) {
      goto(`${base}/404`);
    }
    console.log("Route: ", `${route} is allowed`);

    // Log auth status from the new store in development mode if needed
    if (import.meta.env.DEV) {
      console.log(
        "DEBUG DEV: Auth Status from Store:",
        $isAuthenticated,
        "User:",
        $userEmail,
      );
    }

    // EE Plugin injection - only loaded in EE builds via Vite alias
    // In OSS builds, this import will fail silently
    if ($isAuthenticated) {
      try {
        const { registerEE } = await import("virtual:ee-plugin");
        await registerEE({
          selectedTheme,
          features: [],
        });
        console.log("[EE] Enterprise features loaded");
      } catch {
        // OSS build - no EE plugin available, this is expected
      }
    }
  });
</script>

<svelte:head>
  <title>{$selectedTheme.title}</title>
  <link rel="icon" href={$selectedTheme.favicon} />
</svelte:head>

<div
  class={`flex flex-col bg-theme-light-bg dark:bg-theme-dark-bg ${$page.url.pathname === "/" ? "test" : "h-screen max-h-screen overflow-hidden"}`}
>
  <Navbar />
  <main class="flex-grow overflow-hidden">
    <slot></slot>
  </main>
</div>

<ModalLoggedOut></ModalLoggedOut>
<ModalErrorMessage />
<Toast />
<!--    <DjangoContextDebug/>-->
