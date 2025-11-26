<script lang="ts">
  import { onMount } from "svelte";
  import DarkLightToggle from "$components/DarkLightToggle.svelte";

  // EE extension component - dynamically loaded in EE builds
  let EEThemeSelector: typeof import("svelte").SvelteComponent | null = null;

  onMount(async () => {
    // Try to load EE appearance extension (theme selector)
    // In OSS builds, this import will fail silently
    // Using variable to prevent Vite static analysis
    const eeModule = "virtual:ee-appearance-extension";
    try {
      const module = await import(/* @vite-ignore */ eeModule);
      EEThemeSelector = module.default;
    } catch {
      // OSS build - no EE extension available, this is expected
    }
  });
</script>

<div class="space-y-6">
  <div>
    <p class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
      Theme
    </p>
    <DarkLightToggle version="advanced" />
  </div>

  <!-- EE Theme Selector - only rendered in EE builds -->
  {#if EEThemeSelector}
    <svelte:component this={EEThemeSelector} />
  {/if}
</div>
