<script lang="ts">
  import { onMount, createEventDispatcher } from "svelte";
  import { repositoriesStore } from "$lib/store/github/repositories.store";
  import { ViewTypeEnum } from "./ViewTypes";
  import GitHubAppInstaller from "./GitHubAppInstaller.svelte";
  import { Toggle } from "flowbite-svelte";

  // Add a prop to control whether to show only private repos
  export let privateOnly = true;

  // Create event dispatcher for communicating with parent
  const dispatch = createEventDispatcher();

  onMount(() => {
    // Fetch repositories when component is mounted
    repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
      console.error("Failed to load repositories:", err);
    });
  });

  function formatDate(dateString: string): string {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  // Handler for refresh button
  function refreshRepositories() {
    repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
      console.error("Failed to refresh repositories:", err);
    });
  }

  // Handler for switching to installations view
  function switchToInstallations() {
    dispatch("viewTypeChange", { viewType: ViewTypeEnum.Installations });
  }

  // Handler for installation completion
  function handleInstallationComplete(installationId: string) {
    console.log("Installation completed:", installationId);
    // Refresh repositories after installation
    repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
      console.error("Failed to refresh repositories after installation:", err);
    });
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
            GitHub Repositories
          </h1>
          <p class="mt-1 text-sm text-gray-500 dark:text-gray-300">
            Repositories available through your GitHub App installations
          </p>
        </div>
        <div>
          <Toggle
            label="Private only"
            bind:checked={privateOnly}
            class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-gray-700 bg-gray-100 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            on:change={refreshRepositories}
          />

          <button
            on:click={refreshRepositories}
            class="inline-flex items-center px-3 py-1.5 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            disabled={$repositoriesStore.loading}
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
            {$repositoriesStore.loading ? "Refreshing..." : "Refresh"}
          </button>
        </div>
      </div>

      <div class="flex justify-center m-4">
        <GitHubAppInstaller
          showHeader={false}
          onInstallationComplete={handleInstallationComplete}
        />
      </div>

      <div class="border-t border-gray-200">
        {#if $repositoriesStore.loading}
          <div class="flex justify-center items-center py-12">
            <div
              class="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-indigo-500"
            ></div>
          </div>
        {:else if $repositoriesStore.error}
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
                  Error Loading Repositories
                </h3>
                <div class="mt-2 text-sm text-red-700">
                  <p>{$repositoriesStore.error}</p>
                </div>
              </div>
            </div>
          </div>
        {:else if $repositoriesStore.repositories.length > 0}
          <ul class="divide-y divide-gray-200">
            {#each $repositoriesStore.repositories as repo}
              <li>
                <a
                  href={`/analyse-repo/${repo.owner.login}/${repo.name}`}
                  class="block hover:bg-gray-50 dark:hover:bg-gray-800"
                >
                  <div class="px-4 py-4 sm:px-6">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center">
                        <p
                          class="text-sm font-medium text-gray-800 dark:text-gray-200 truncate"
                        >
                          {repo.owner.login}/{repo.name}
                        </p>

                        {#if repo.private}
                          <span
                            class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200"
                          >
                            Private
                          </span>
                        {/if}

                        {#if repo.language}
                          <span
                            class="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100"
                          >
                            {repo.language}
                          </span>
                        {/if}
                      </div>
                      <div class="ml-2 flex-shrink-0 flex">
                        <span
                          class="inline-flex items-center text-xs text-gray-500 dark:text-gray-400"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-4 w-4 mr-1"
                            fill="none"
                            viewBox="0 0 24 24"
                            stroke="currentColor"
                          >
                            <path
                              stroke-linecap="round"
                              stroke-linejoin="round"
                              stroke-width="2"
                              d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"
                            />
                          </svg>
                          {repo.stargazers_count}
                        </span>
                      </div>
                    </div>
                    <div class="mt-2 sm:flex sm:justify-between">
                      <div class="sm:flex">
                        <p
                          class="flex items-center text-sm text-gray-500 dark:text-gray-400"
                        >
                          {repo.description || "No description"}
                        </p>
                      </div>
                      <div
                        class="mt-2 flex items-center text-sm text-gray-500 dark:text-gray-400 sm:mt-0"
                      >
                        <svg
                          xmlns="http://www.w3.org/2000/svg"
                          class="flex-shrink-0 mr-1.5 h-5 w-5 text-gray-400"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                        <p>
                          Updated {formatDate(repo.updated_at)}
                        </p>
                      </div>
                    </div>

                    {#if repo.open_issues_count > 0}
                      <div class="mt-2">
                        <span
                          class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100"
                        >
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="h-3.5 w-3.5 mr-1"
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
                          {repo.open_issues_count} Open {repo.open_issues_count ===
                          1
                            ? "Issue"
                            : "Issues"}
                        </span>
                      </div>
                    {/if}
                  </div>
                </a>
              </li>
            {/each}
          </ul>
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
                d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"
              />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              No repositories found
            </h3>
            <p class="mt-1 text-sm text-gray-500 dark:text-gray-400">
              No repositories available through your GitHub App installations.
            </p>
            <div class="mt-6">
              <!-- TODO: when this is clicked, please switch to the Installations viewtype -->
              <button
                on:click={switchToInstallations}
                class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-indigo-700 bg-indigo-100 hover:bg-indigo-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 dark:bg-indigo-900 dark:text-indigo-100 dark:hover:bg-indigo-800"
              >
                View Installations
              </button>
            </div>
          </div>
        {/if}

        {#if $repositoriesStore.lastFetched}
          <div
            class="px-4 py-2 text-xs text-gray-500 dark:text-gray-400 text-right border-t border-gray-100"
          >
            Last updated: {$repositoriesStore.lastFetched.toLocaleTimeString()}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>
