<script lang="ts">
  import { onMount } from "svelte";
  import type { GitHubInstallationsResponse } from "$lib/types/github/installation";
  import { format } from "date-fns";

  // State
  let isLoading = true;
  let error: string | null = null;
  let installationsData: GitHubInstallationsResponse | null = null;

  // Format date from ISO string to readable format
  function formatDate(dateStr: string): string {
    try {
      return format(new Date(dateStr), "MMM d, yyyy");
    } catch (e) {
      return dateStr;
    }
  }

  // Handle installation button click
  async function handleInstallClick() {
    try {
      // TODO: goto the installation url to be able to add github app
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = "An unknown error occurred";
      }
    }
  }

  // Load installations data
  onMount(async () => {
    try {
      // this installation stuff needs proper fixing
      // installationsData = await fetchGitHubInstallations();
    } catch (err) {
      if (err instanceof Error) {
        error = err.message;
      } else {
        error = "An unknown error occurred";
      }
    } finally {
      isLoading = false;
    }
  });
</script>

<div class="py-8">
  <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
    <div
      class="bg-white dark:bg-gray-900 dark:text-white shadow overflow-hidden rounded-lg"
    >
      <div class="px-4 py-5 sm:px-6">
        <h1 class="text-xl font-medium text-gray-900 dark:text-white">
          GitHub App Installations
        </h1>
        <p class="mt-1 text-sm text-gray-500 dark:text-gray-200">
          View and manage your GitHub App installations
        </p>
      </div>

      {#if isLoading}
        <div class="px-4 py-5 sm:p-6 flex justify-center">
          <div
            class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-600"
          ></div>
        </div>
      {:else if error}
        <div class="px-4 py-5 sm:p-6 text-red-500">
          <p>Error: {error}</p>
        </div>
      {:else if installationsData}
        {#if installationsData.is_connected && installationsData.social_account}
          <div class="px-4 py-3 sm:px-6 bg-gray-50 dark:bg-gray-900">
            <div class="flex items-center">
              <img
                src={installationsData.social_account.avatar_url}
                alt={installationsData.social_account.login}
                class="h-8 w-8 rounded-full mr-2"
              />
              <span class="text-sm font-medium text-gray-600 dark:text-white">
                Connected as: {installationsData.social_account.login}
              </span>
            </div>
          </div>

          <div class="px-4 py-5 sm:p-6">
            {#if installationsData.installations.length > 0}
              <div class="flow-root">
                <ul class="divide-y divide-gray-200">
                  {#each installationsData.installations as install}
                    <li class="py-4">
                      <div class="flex items-center space-x-4">
                        <div class="flex-1 min-w-0">
                          <p
                            class="text-sm font-medium text-gray-900 dark:text-white truncate"
                          >
                            {install.account_name}
                          </p>
                          <p class="text-sm text-gray-500 dark:text-gray-400">
                            {install.account_type.charAt(0).toUpperCase() +
                              install.account_type.slice(1)} • Installed: {formatDate(
                              install.installed_at,
                            )}
                          </p>
                          <p
                            class="mt-1 text-xs text-gray-500 dark:text-gray-400"
                          >
                            Installation ID: {install.installation_id}
                          </p>
                        </div>
                      </div>
                    </li>
                  {/each}
                </ul>
              </div>
            {:else}
              <div class="text-center py-6">
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
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                  />
                </svg>
                <h3
                  class="mt-2 text-sm font-medium text-gray-900 dark:text-white"
                >
                  No installations found
                </h3>
                <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
                  You haven't installed the GitHub App yet.
                </p>
                <div class="mt-6">
                  <button
                    on:click={handleInstallClick}
                    class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
                  >
                    Install GitHub App
                  </button>
                </div>
              </div>
            {/if}
          </div>

          {#if installationsData.installations.length > 0}
            <div class="flex md:gap-4 m-4">
              <button
                on:click={handleInstallClick}
                class="text-white bg-gradient-to-r from-green-400 via-green-500 to-green-600 hover:bg-gradient-to-br focus:ring-4 focus:outline-none focus:ring-green-300 dark:focus:ring-green-800 font-medium rounded-lg text-sm px-5 py-2.5 text-center me-2 mb-2"
              >
                Add Installation
              </button>

              <a
                href="/github/repositories"
                class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 text-center me-2 mb-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800"
              >
                View My Repos
              </a>
            </div>
          {/if}
        {:else}
          <div class="px-4 py-5 sm:p-6 text-center">
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
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              Not connected to GitHub
            </h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              You need to connect your GitHub account first.
            </p>
            <div class="mt-6">
              <a
                href="/account/social-connections"
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                Connect GitHub Account
              </a>
            </div>
          </div>
        {/if}
      {/if}
    </div>
  </div>
</div>
