<script lang="ts">
  import { onMount } from "svelte";
  import { installationsStore } from "$lib/store/github/installations.store";
  import { getInstallationUrl } from "$lib/apis/github/api.github";

  // Component props
  export let showHeader = true;

  // Component state
  let installing = false;
  let error: string | null = null;
  let installUrl = "";
  let installState = "";

  // Installation states - simplified since callback is handled elsewhere
  type InstallationStep = "idle" | "generating-url" | "redirecting" | "error";
  let currentStep: InstallationStep = "idle";

  onMount(() => {
    // No longer need to handle callbacks here - they're handled by the dedicated callback route
  });

  async function startInstallation() {
    if (installing) return;

    try {
      installing = true;
      currentStep = "generating-url";
      error = null;

      // Get installation URL from our API
      const data = await getInstallationUrl();

      if (!data.install_url) {
        throw new Error("No installation URL received");
      }

      installUrl = data.install_url;
      installState = data.state;
      currentStep = "redirecting";

      // Add callback URL parameter to the installation URL - use dedicated callback route
      const callbackUrl = encodeURIComponent(
        `${window.location.origin}/github/app/callback`,
      );
      const finalUrl = `${installUrl}&callback_url=${callbackUrl}`;

      // Redirect to GitHub for installation
      window.location.href = finalUrl;
    } catch (err) {
      console.error("Installation error:", err);
      error =
        err instanceof Error ? err.message : "Failed to start installation";
      currentStep = "error";
      installing = false;
    }
  }

  function resetInstallation() {
    currentStep = "idle";
    installing = false;
    error = null;
    installUrl = "";
    installState = "";
  }

  function getStepMessage(step: InstallationStep): string {
    switch (step) {
      case "idle":
        return "Ready to install";
      case "generating-url":
        return "Preparing installation...";
      case "redirecting":
        return "Redirecting to GitHub...";
      case "error":
        return "Installation failed";
      default:
        return "";
    }
  }
</script>

{#if showHeader}
  <div class="mb-6">
    <h2 class="text-lg font-medium text-gray-900 dark:text-white">
      XInstall GitHub App
    </h2>
    <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
      Install the GitHub App to enable repository access and automation
      features.
    </p>
  </div>
{/if}

<div class="bg-white dark:bg-gray-900 shadow rounded-lg p-6">
  {#if currentStep === "idle"}
    <div class="text-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mx-auto h-12 w-12 text-gray-400 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 6v6m0 0v6m0-6h6m-6 0H6"
        />
      </svg>

      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        Install GitHub App
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400 mb-6">
        Click the button below to install the GitHub App on your repositories.
      </p>

      <button
        on:click={startInstallation}
        disabled={installing}
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="-ml-1 mr-2 h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          />
        </svg>
        Install GitHub App
      </button>
    </div>
  {:else if currentStep === "error"}
    <div class="text-center">
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="mx-auto h-12 w-12 text-red-400 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>

      <h3 class="text-lg font-medium text-red-800 dark:text-red-400 mb-2">
        Installation Failed
      </h3>
      {#if error}
        <p class="text-sm text-red-600 dark:text-red-400 mb-6">
          {error}
        </p>
      {/if}

      <button
        on:click={resetInstallation}
        class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-red-600 hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
      >
        Try Again
      </button>
    </div>
  {:else}
    <div class="text-center">
      <div
        class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500 mx-auto mb-4"
      ></div>

      <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
        {getStepMessage(currentStep)}
      </h3>
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Please wait while we process your installation...
      </p>
    </div>
  {/if}
</div>
