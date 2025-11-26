<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";

  // OSS: Always redirect to login page
  // EE builds override this entire page via Vite alias
  onMount(() => {
    goto(`${base}/login`);
  });
</script>

<svelte:head>
  <title>Holly - Open Source AI-Powered Code Analysis Platform</title>
  <meta
    name="description"
    content="Open source AI-powered code analysis platform with multiple LLM support, GitHub integration, and automated PR generation"
  />
</svelte:head>

<!-- OSS: Show loading while redirecting to login -->
<div class="flex items-center justify-center min-h-screen bg-theme-light-bg dark:bg-gray-900">
  <div class="text-center">
    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary mx-auto mb-4"></div>
    <p class="text-gray-600 dark:text-gray-400">Redirecting...</p>
  </div>
</div>
