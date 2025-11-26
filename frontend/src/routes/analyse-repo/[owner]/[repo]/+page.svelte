<script lang="ts">
  import { page } from "$app/stores";
  import { onMount } from "svelte";
  import type { GitHubRepository } from "$lib/types/github/repository";

  // Extract the owner and repo from the URL parameters
  const owner = $page.params.owner;
  const repo = $page.params.repo;

  let repository: GitHubRepository | null = null;
  let loading = true;
  let error: string | null = null;

  onMount(async () => {
    try {
      // In a real implementation, this would be an API call to get repository details
      // For now, we'll just redirect to the repository URL as a placeholder
      // Redirect to GitHub repository page until this page is implemented
      window.location.href = `https://github.com/${owner}/${repo}`;
    } catch (err) {
      console.error("Failed to load repository details:", err);
      error =
        err instanceof Error
          ? err.message
          : "Failed to load repository details";
      loading = false;
    }
  });
</script>

<div class="container mx-auto px-4 py-8">
  <div class="max-w-3xl mx-auto">
    <div class="bg-white dark:bg-gray-900 shadow rounded-lg p-6">
      {#if loading}
        <div class="flex items-center justify-center py-12">
          <div
            class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"
          ></div>
        </div>
        <p class="text-center text-gray-500 dark:text-gray-400">
          Redirecting to GitHub repository...
        </p>
      {:else if error}
        <div class="bg-red-50 border border-red-100 rounded-md p-4">
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
                Error Loading Repository
              </h3>
              <div class="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      {/if}

      <div class="mt-4 flex justify-center">
        <a
          href="/github"
          class="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
        >
          ← Back to repositories
        </a>
      </div>
    </div>
  </div>
</div>
