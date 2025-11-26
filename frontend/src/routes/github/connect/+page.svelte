<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { isAuthenticated } from "$lib/store/auth/tokens.store";
  import {
    getGitHubConnectionStatus,
    startGitHubOAuthFlow,
  } from "$lib/apis/users/github-oauth";
  import GitHubApiDebugger from "$lib/apis/debug/github-api-debugger";
  import { navigateToAdvanced } from "$components";

  let isGitHubConnected = false;
  let isLoading = true;
  let errorLoading = false;
  let errorMessage = "";
  let userName: string | null = null;
  let userAvatarUrl: string | null = null;
  let totalAccounts = 0;

  onMount(async () => {
    if (!browser) return;

    // Make debugger available in console during development
    if (import.meta.env.DEV) {
      (window as any).GitHubApiDebugger = GitHubApiDebugger;
    }

    if (!$isAuthenticated) {
      console.log("🔍 User not authenticated, skipping GitHub status check");
      isLoading = false;
      return;
    }

    try {
      console.log("🔍 Checking GitHub connection status...");
      const response = await getGitHubConnectionStatus();
      console.log("✅ GitHub connection status retrieved:", response);

      if (response && response.is_connected) {
        isGitHubConnected = true;
        totalAccounts = response.total_accounts;

        if (response.primary_account) {
          userName = response.primary_account.github_login;
          userAvatarUrl = response.primary_account.avatar_url;
        }
      }
    } catch (err) {
      console.error("❌ Error checking GitHub connection status");
      errorLoading = true;

      // Set a user-friendly error message based on the error type
      if (
        typeof err === "object" &&
        err !== null &&
        "status" in err &&
        err.status === 401
      ) {
        errorMessage = "Authentication failed. Please try logging in again.";
      } else {
        errorMessage =
          "Could not load GitHub connection status. Please try again later.";
      }
    } finally {
      isLoading = false;
    }
  });

  async function connectToGitHub() {
    if (!browser) return;

    try {
      isLoading = true;
      errorLoading = false;
      errorMessage = "";

      console.log("🔍 Starting GitHub OAuth flow...");
      // Use the new API-based OAuth flow
      await startGitHubOAuthFlow("/github/connect");
    } catch (error) {
      console.error("❌ Error connecting to GitHub");
      errorLoading = true;

      if (
        typeof error === "object" &&
        error !== null &&
        "status" in error &&
        error.status === 401
      ) {
        errorMessage = "Authentication failed. Please try logging in again.";
      } else {
        errorMessage = "Could not connect to GitHub. Please try again later.";
      }

      isLoading = false;
    }
  }

  // Debug function for testing (only in dev mode)
  async function runDebugTest() {
    if (import.meta.env.DEV) {
      await GitHubApiDebugger.testGitHubConnectionStatus();
    }
  }
</script>

<div class="container mx-auto p-4 max-w-md">
  <div class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <h1 class="text-xl font-bold mb-6 text-center">Connect to GitHub</h1>

    {#if isLoading}
      <div class="flex justify-center items-center py-4">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
        ></div>
        <p class="ml-3 text-gray-700">Loading connection status...</p>
      </div>
    {:else if errorLoading}
      <div
        class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
        role="alert"
      >
        <strong class="font-bold">Error!</strong>
        <span class="block sm:inline">
          {errorMessage ||
            "Could not load GitHub connection status. Please try again later."}</span
        >
        <details class="mt-2">
          <summary class="cursor-pointer text-sm underline"
            >Show debugging info</summary
          >
          <div class="mt-2 text-xs">
            <p>If this error persists, please check:</p>
            <ul class="list-disc ml-4 mt-1">
              <li>Your internet connection</li>
              <li>Try refreshing the page</li>
              <li>Try logging out and back in</li>
              <li>Check browser console for more details</li>
            </ul>
          </div>
        </details>
      </div>
    {:else if !$isAuthenticated}
      <div
        class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-4"
        role="alert"
      >
        <strong class="font-bold">Authentication Required</strong>
        <span class="block sm:inline">
          You need to be logged in to connect your GitHub account.</span
        >
      </div>
    {:else if isGitHubConnected}
      <div class="text-center py-4">
        {#if userAvatarUrl}
          <img
            src={userAvatarUrl}
            alt="{userName || 'GitHub User'}'s avatar"
            class="w-20 h-20 rounded-full mx-auto mb-4 border-2 border-gray-300"
          />
        {/if}
        <p class="text-lg font-semibold text-green-700">
          Your GitHub account is already connected!
        </p>
        {#if userName}
          <p class="text-md text-gray-800">
            Connected as: <strong class="font-medium">{userName}</strong>
          </p>
        {/if}
        {#if totalAccounts > 1}
          <p class="text-sm text-gray-600 mt-2">
            You have {totalAccounts} GitHub accounts connected.
          </p>
        {/if}
        <div class="mt-6 space-y-3">
          <button
            on:click={navigateToAdvanced}
            class="w-full bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Start Vibe Coding
          </button>
          <a
            href="/github/accounts"
            class="block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Manage GitHub Accounts
          </a>
          {#if import.meta.env.DEV}
            <button
              on:click={runDebugTest}
              class="block w-full bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out text-sm"
            >
              🔧 Debug API Test
            </button>
          {/if}
        </div>
      </div>
    {:else}
      <p class="mb-6 text-gray-700 text-center">
        Link your GitHub account to allow us to access your repositories. This
        will redirect you to GitHub for authorization.
      </p>
      <button
        on:click={connectToGitHub}
        class="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-3 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out"
      >
        Connect to GitHub
      </button>
      {#if import.meta.env.DEV}
        <button
          on:click={runDebugTest}
          class="w-full mt-3 bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-150 ease-in-out text-sm"
        >
          🔧 Debug API Test
        </button>
      {/if}
    {/if}
  </div>
</div>

<style>
  .container {
  }
</style>
