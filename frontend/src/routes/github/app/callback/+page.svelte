<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { handleInstallationCallback } from "$lib/apis/github/api.github";
  import { installationsStore } from "$lib/store/github/installations.store";

  let isProcessing = true;
  let success = false;
  let errorMessage = "";
  let successMessage = "";
  let installationId: string | null = null;
  let redirectUrl = "/github/installations";

  onMount(async () => {
    if (!browser) return;

    const urlParams = new URLSearchParams(window.location.search);
    const installationIdParam = urlParams.get("installation_id");
    const state = urlParams.get("state");
    const setupAction = urlParams.get("setup_action");

    // Handle GitHub App installation errors
    if (setupAction === "install" && !installationIdParam) {
      isProcessing = false;
      errorMessage = "Installation was cancelled or failed";
      return;
    }

    // Check for required parameters
    if (!installationIdParam || !state) {
      isProcessing = false;
      errorMessage =
        "Missing required installation parameters (installation_id or state)";
      return;
    }

    try {
      installationId = installationIdParam;

      // Process the GitHub App installation callback
      const response = await handleInstallationCallback({
        installation_id: installationIdParam,
        state: state,
      });

      success = response.success;
      successMessage = response.message;

      if (!success) {
        errorMessage = response.message;
      } else {
        // Refresh the installations store
        await installationsStore.fetchInstallations();
      }
    } catch (err) {
      console.error("Error processing GitHub App installation callback:", err);
      success = false;
      errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
    } finally {
      isProcessing = false;
      // Clean up URL parameters
      if (browser) {
        window.history.replaceState({}, "", window.location.pathname);
      }
    }
  });

  function redirectToInstallations() {
    if (browser) {
      goto(redirectUrl);
    }
  }

  function redirectToRepositories() {
    if (browser) {
      goto("/github");
    }
  }
</script>

<svelte:head>
  <title>GitHub App Installation - GitHubMe</title>
</svelte:head>

<div class="container mx-auto p-4 max-w-md">
  <div class="bg-white dark:bg-gray-800 shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <h1
      class="text-xl font-bold mb-6 text-center text-gray-900 dark:text-white"
    >
      GitHub App Installation
    </h1>

    {#if isProcessing}
      <div class="flex justify-center items-center py-8">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"
        ></div>
        <p class="ml-4 text-gray-700 dark:text-gray-300">
          Processing your GitHub App installation...
        </p>
      </div>
    {:else if success}
      <div class="text-center py-4">
        <div class="mb-4">
          <svg
            class="w-16 h-16 text-green-500 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            ></path>
          </svg>
        </div>

        <h2
          class="text-lg font-semibold text-green-700 dark:text-green-400 mb-2"
        >
          Installation Successful!
        </h2>
        <p class="text-gray-700 dark:text-gray-300 mb-4">{successMessage}</p>

        {#if installationId}
          <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mb-4">
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Installation ID: <span
                class="font-mono text-blue-600 dark:text-blue-400"
                >{installationId}</span
              >
            </p>
          </div>
        {/if}

        <div class="space-y-3">
          <button
            on:click={redirectToRepositories}
            class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            View My Repositories
          </button>

          <button
            on:click={redirectToInstallations}
            class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Manage Installations
          </button>
        </div>
      </div>
    {:else}
      <div class="text-center py-4">
        <div class="mb-4">
          <svg
            class="w-16 h-16 text-red-500 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M6 18L18 6M6 6l12 12"
            ></path>
          </svg>
        </div>

        <h2 class="text-lg font-semibold text-red-700 dark:text-red-400 mb-2">
          Installation Failed
        </h2>
        <p class="text-gray-700 dark:text-gray-300 mb-4">{errorMessage}</p>

        <div class="space-y-3">
          <button
            on:click={redirectToInstallations}
            class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Try Again
          </button>

          <button
            on:click={redirectToRepositories}
            class="w-full bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Back to GitHub
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
