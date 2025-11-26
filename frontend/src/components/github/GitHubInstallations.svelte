<script lang="ts">
  import { onMount } from "svelte";
  import { installationsStore } from "$lib/store/github/installations.store";
  import GitHubAppInstaller from "./GitHubAppInstaller.svelte";
  import type { GitHubInstallation } from "$lib/types/github/installation";

  onMount(() => {
    // Fetch installations when component is mounted
    installationsStore.fetchInstallations().catch((err) => {
      console.error("Failed to load installations:", err);
    });
  });

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  // Handler for refresh button
  function refreshInstallations() {
    installationsStore.fetchInstallations().catch((err) => {
      console.error("Failed to refresh installations:", err);
    });
  }

  // Handler for installation completion
  function handleInstallationComplete(installationId: string) {
    console.log("Installation completed:", installationId);
    // The store is already refreshed by the installer component
  }

  // Handler for manage button - opens GitHub app management page
  function handleManageInstallation(installation: GitHubInstallation) {
    const { installation_id, account_type, account_name } = installation;

    let githubUrl: string;
    if (account_type === "organization") {
      githubUrl = `https://github.com/organizations/${account_name}/settings/installations/${installation_id}`;
    } else {
      githubUrl = `https://github.com/settings/installations/${installation_id}`;
    }

    // Open GitHub management page in new tab
    window.open(githubUrl, "_blank", "noopener,noreferrer");
  }
</script>

<div class="py-8">
  <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
    <div
      class="bg-white dark:bg-gray-900 dark:text-white shadow overflow-hidden rounded-lg"
    >
      <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
        <div>
          <h1 class="text-xl font-medium text-gray-900 dark:text-white">
            GitHub App Installations
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-300">
            Manage your GitHub App installations
          </p>
        </div>

        <button
          on:click={refreshInstallations}
          class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          disabled={$installationsStore.loading}
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="-ml-0.5 mr-2 h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          {$installationsStore.loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <!-- User profile info if connected -->
      {#if $installationsStore.isConnected && $installationsStore.socialAccount}
        <div
          class="px-4 py-3 border-t border-gray-200 bg-gray-50 dark:bg-gray-800 dark:border-gray-700"
        >
          <div class="flex items-center space-x-3">
            <img
              src={$installationsStore.socialAccount.avatar_url}
              alt="GitHub Profile"
              class="h-10 w-10 rounded-full"
            />
            <div>
              <h3 class="text-sm font-medium text-gray-900 dark:text-white">
                Connected as {$installationsStore.socialAccount.login}
              </h3>
              <p class="text-xs text-gray-500 dark:text-gray-400">
                GitHub account connected successfully
              </p>
            </div>
          </div>
        </div>
      {/if}

      <div class="border-t border-gray-200">
        {#if $installationsStore.loading}
          <div class="flex justify-center items-center py-12">
            <div
              class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"
            ></div>
          </div>
        {:else if $installationsStore.error}
          <div
            class="px-4 py-5 sm:px-6 bg-red-50 border-t border-b border-red-100"
          >
            <div class="flex">
              <div class="flex-shrink-0">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-5 w-5 text-red-400"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fill-rule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-red-800">
                  Error Loading Installations
                </h3>
                <div class="mt-2 text-sm text-red-700">
                  <p>{$installationsStore.error}</p>
                </div>
              </div>
            </div>
          </div>
        {:else if !$installationsStore.isConnected}
          <div class="text-center py-12">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              Not connected to GitHub
            </h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Connect your GitHub account to manage repositories.
            </p>
            <div class="mt-6">
              <a
                href="/github/connect"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Connect to GitHub
              </a>
            </div>
          </div>
        {:else if $installationsStore.installations.length > 0}
          <ul class="divide-y divide-gray-200">
            {#each $installationsStore.installations as installation}
              <li class="px-4 py-4 sm:px-6">
                <div class="flex items-center justify-between">
                  <div class="flex items-center">
                    <div class="min-w-0 flex-1">
                      <p
                        class="text-sm font-medium text-gray-900 dark:text-white truncate"
                      >
                        {installation.account_name}
                      </p>
                      <p class="text-xs text-gray-500 dark:text-gray-400">
                        Type: {installation.account_type === "organization"
                          ? "Organization"
                          : "User"}
                      </p>
                      <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
                        Installed at: {formatDate(installation.installed_at)}
                      </p>
                    </div>
                  </div>
                  <div class="ml-4 flex-shrink-0 flex">
                    <button
                      on:click={() => handleManageInstallation(installation)}
                      class="inline-flex items-center px-2.5 py-1.5 border border-gray-300 shadow-sm text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-gray-700 dark:text-white dark:border-gray-600 dark:hover:bg-gray-600"
                      title="Manage repository access on GitHub"
                    >
                      <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="w-3 h-3 mr-1"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="2"
                          d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                        />
                      </svg>
                      Manage
                    </button>
                  </div>
                </div>
              </li>
            {/each}
          </ul>
          <div class="mt-6 border-t border-gray-200">
            <GitHubAppInstaller
              showHeader={false}
              onInstallationComplete={handleInstallationComplete}
            />
          </div>
        {:else}
          <div class="text-center py-12">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              No installations found
            </h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You haven't installed the GitHub App on any repositories yet.
            </p>
            <div class="mt-6">
              <GitHubAppInstaller
                showHeader={false}
                onInstallationComplete={handleInstallationComplete}
              />
            </div>
          </div>
        {/if}

        {#if $installationsStore.lastFetched}
          <div
            class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 text-right border-t border-gray-100"
          >
            Last updated: {$installationsStore.lastFetched.toLocaleTimeString()}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
