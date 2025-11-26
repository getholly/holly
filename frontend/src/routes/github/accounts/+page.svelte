<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";
  import { isAuthenticated } from "$lib/store/auth/tokens.store";
  import {
    listGitHubAccounts,
    disconnectGitHubAccount,
    setPrimaryGitHubAccount,
    startGitHubOAuthFlow,
  } from "$lib/apis/users/github-oauth";
  import { navigateToAdvanced } from "$components";

  let accounts: any[] = [];
  let isLoading = true;
  let errorMessage = "";
  let successMessage = "";
  let isProcessing = false;

  onMount(async () => {
    if (!browser) return;

    if (!$isAuthenticated) {
      isLoading = false;
      return;
    }

    await loadAccounts();
  });

  async function loadAccounts() {
    try {
      isLoading = true;
      errorMessage = "";

      const response = await listGitHubAccounts();
      accounts = response.accounts || [];
    } catch (err) {
      console.error("Error loading GitHub accounts:", err);
      errorMessage =
        err instanceof Error ? err.message : "Failed to load GitHub accounts";
    } finally {
      isLoading = false;
    }
  }

  async function handleDisconnect(githubLogin: string) {
    if (
      !confirm(
        `Are you sure you want to disconnect the GitHub account "${githubLogin}"?`,
      )
    ) {
      return;
    }

    try {
      isProcessing = true;
      errorMessage = "";
      successMessage = "";

      const response = await disconnectGitHubAccount(githubLogin);

      if (response.success) {
        successMessage = response.message;
        await loadAccounts(); // Reload the accounts list
      } else {
        errorMessage = response.message;
      }
    } catch (err) {
      console.error("Error disconnecting GitHub account:", err);
      errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to disconnect GitHub account";
    } finally {
      isProcessing = false;
    }
  }

  async function handleSetPrimary(githubLogin: string) {
    try {
      isProcessing = true;
      errorMessage = "";
      successMessage = "";

      const response = await setPrimaryGitHubAccount(githubLogin);

      if (response.success) {
        successMessage = response.message;
        await loadAccounts(); // Reload the accounts list
      } else {
        errorMessage = response.message;
      }
    } catch (err) {
      console.error("Error setting primary GitHub account:", err);
      errorMessage =
        err instanceof Error
          ? err.message
          : "Failed to set primary GitHub account";
    } finally {
      isProcessing = false;
    }
  }

  async function handleAddAccount() {
    try {
      await startGitHubOAuthFlow("/github/accounts");
    } catch (error) {
      console.error("Error starting GitHub OAuth flow:", error);
      errorMessage = "Failed to start GitHub connection process";
    }
  }

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
</script>

<svelte:head>
  <title>Manage GitHub Accounts - GitHubMe</title>
</svelte:head>

<div class="container mx-auto p-4 max-w-4xl">
  <div class="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <div class="flex justify-between items-center mb-6">
      <h1 class="text-2xl font-bold">Manage GitHub Accounts</h1>
      <button
        on:click={handleAddAccount}
        class="bg-green-500 hover:bg-green-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
        disabled={isProcessing}
      >
        <svg
          class="w-4 h-4 inline mr-2"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 6v6m0 0v6m0-6h6m-6 0H6"
          ></path>
        </svg>
        Connect Another Account
      </button>
    </div>

    {#if !$isAuthenticated}
      <div
        class="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative mb-4"
        role="alert"
      >
        <strong class="font-bold">Authentication Required</strong>
        <span class="block sm:inline">
          You need to be logged in to manage your GitHub accounts.</span
        >
      </div>
    {:else if isLoading}
      <div class="flex justify-center items-center py-8">
        <div
          class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"
        ></div>
        <p class="ml-3 text-gray-700">Loading your GitHub accounts...</p>
      </div>
    {:else}
      <!-- Success/Error Messages -->
      {#if successMessage}
        <div
          class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <span class="block sm:inline">{successMessage}</span>
        </div>
      {/if}

      {#if errorMessage}
        <div
          class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4"
          role="alert"
        >
          <strong class="font-bold">Error!</strong>
          <span class="block sm:inline"> {errorMessage}</span>
        </div>
      {/if}

      {#if accounts.length === 0}
        <div class="text-center py-8">
          <svg
            class="w-16 h-16 text-gray-400 mx-auto mb-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            ></path>
          </svg>
          <h3 class="text-lg font-semibold text-gray-700 mb-2">
            No GitHub Accounts Connected
          </h3>
          <p class="text-gray-600 mb-4">
            Connect your first GitHub account to get started.
          </p>
          <button
            on:click={handleAddAccount}
            class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Connect GitHub Account
          </button>
        </div>
      {:else}
        <div class="space-y-4">
          {#each accounts as account (account.github_login)}
            <div
              class="border rounded-lg p-4 bg-gray-50 {account.is_primary
                ? 'border-green-500 bg-green-50'
                : 'border-gray-200'}"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  {#if account.avatar_url}
                    <img
                      src={account.avatar_url}
                      alt="{account.github_login}'s avatar"
                      class="w-12 h-12 rounded-full mr-4 border-2 border-gray-300"
                    />
                  {/if}
                  <div>
                    <div class="flex items-center">
                      <h3 class="text-lg font-semibold">
                        {account.github_login}
                      </h3>
                      {#if account.is_primary}
                        <span
                          class="ml-2 bg-green-500 text-white text-xs px-2 py-1 rounded"
                          >Primary</span
                        >
                      {/if}
                    </div>
                    <p class="text-sm text-gray-600">ID: {account.github_id}</p>
                    <p class="text-sm text-gray-600">
                      Connected: {formatDate(account.created_at)}
                    </p>
                  </div>
                </div>

                <div class="flex space-x-2">
                  {#if !account.is_primary}
                    <button
                      on:click={() => handleSetPrimary(account.github_login)}
                      class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-1 px-3 rounded text-sm transition duration-150 ease-in-out"
                      disabled={isProcessing}
                    >
                      Set Primary
                    </button>
                  {/if}

                  <button
                    on:click={() => handleDisconnect(account.github_login)}
                    class="bg-red-500 hover:bg-red-600 text-white font-bold py-1 px-3 rounded text-sm transition duration-150 ease-in-out"
                    disabled={isProcessing}
                  >
                    {#if isProcessing}
                      <div
                        class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"
                      ></div>
                    {:else}
                      Disconnect
                    {/if}
                  </button>
                </div>
              </div>

              {#if account.is_primary && accounts.length === 1}
                <p class="text-sm text-gray-500 mt-2">
                  Cannot disconnect your only GitHub account. Connect another
                  account first.
                </p>
              {/if}
            </div>
          {/each}
        </div>

        <div class="mt-6 text-center">
          <p class="text-sm text-gray-600">
            You have {accounts.length} GitHub account{accounts.length !== 1
              ? "s"
              : ""} connected.
          </p>
        </div>
      {/if}

      <div class="mt-8 pt-4 border-t border-gray-200">
        <div class="flex justify-center space-x-4">
          <a
            href="/github/connect"
            class="bg-gray-500 hover:bg-gray-600 text-white font-bold py-2 px-4 rounded transition duration-150 ease-in-out"
          >
            Back to Connect
          </a>
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
