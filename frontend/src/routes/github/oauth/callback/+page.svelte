<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { handleGitHubOAuthCallback } from "$lib/apis/users/github-oauth";
  import { navigateToAdvanced } from "$components";

  let isProcessing = true;
  let success = false;
  let errorMessage = "";
  let successMessage = "";
  let accountInfo: any = null;
  let redirectUrl = "/github/connect";

  onMount(async () => {
    if (!browser) return;

    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get("code");
    const state = urlParams.get("state");
    const error = urlParams.get("error");

    // Handle OAuth errors from GitHub
    if (error) {
      isProcessing = false;
      errorMessage = `GitHub OAuth error: ${error}`;
      return;
    }

    // Check for required parameters
    if (!code || !state) {
      isProcessing = false;
      errorMessage = "Missing required OAuth parameters (code or state)";
      return;
    }

    try {
      // Process the OAuth callback
      const response = await handleGitHubOAuthCallback(code, state);

      success = response.success;
      successMessage = response.message;
      accountInfo = response.account_info;

      if (response.redirect_url) {
        redirectUrl = response.redirect_url;
      }

      if (!success) {
        errorMessage = response.message;
      }
    } catch (err) {
      console.error("Error processing OAuth callback:", err);
      success = false;
      errorMessage =
        err instanceof Error ? err.message : "Unknown error occurred";
    } finally {
      isProcessing = false;
    }
  });

  function redirectToConnect() {
    if (browser) {
      goto(redirectUrl);
    }
  }

  function redirectToDashboard() {
    if (browser) {
      goto("/dashboard");
    }
  }
</script>

<svelte:head>
  <title>GitHub OAuth Callback - GitHubMe</title>
</svelte:head>

<div class="container mx-auto p-4 max-w-md">
  <div class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <h1 class="text-xl font-bold mb-6 text-center">Connecting to GitHub</h1>

    {#if isProcessing}
      <div class="flex justify-center items-center py-8">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"
        ></div>
        <p class="ml-4 text-gray-700">Processing your GitHub connection...</p>
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

        <h2 class="text-lg font-semibold text-green-700 mb-2">
          Successfully Connected!
        </h2>
        <p class="text-gray-700 mb-4">{successMessage}</p>

        {#if accountInfo}
          <div class="bg-gray-50 rounded-lg p-4 mb-4">
            <div class="flex items-center justify-center mb-2">
              {#if accountInfo.avatar_url}
                <img
                  src={accountInfo.avatar_url}
                  alt="GitHub Avatar"
                  class="w-12 h-12 rounded-full mr-3"
                />
              {/if}
              <div>
                <p class="font-medium">{accountInfo.github_login}</p>
                {#if accountInfo.is_primary}
                  <p class="text-sm text-green-600">Primary Account</p>
                {/if}
              </div>
            </div>
          </div>
        {/if}

        <div class="space-y-3">
          <button
            on:click={navigateToAdvanced}
            class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Start Vibe Coding
          </button>

          <button
            on:click={redirectToConnect}
            class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Manage GitHub Accounts
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

        <h2 class="text-lg font-semibold text-red-700 mb-2">
          Connection Failed
        </h2>
        <p class="text-gray-700 mb-4">{errorMessage}</p>

        <div class="space-y-3">
          <button
            on:click={redirectToConnect}
            class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Try Again
          </button>

          <button
            on:click={navigateToAdvanced}
            class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Start Vibe Coding
          </button>
        </div>
      </div>
    {/if}
  </div>
</div>
