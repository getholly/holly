<script lang="ts">
  import GitHubRepositoryList from "./GitHubRepositoryList.svelte";
  import GitHubRepositoryGrid from "./GitHubRepositoryGrid.svelte";
  import GitHubInstallations from "./GitHubInstallations.svelte";
  import GitHubAppViewToggle from "./GitHubAppViewToggle.svelte";
  import { ViewTypeEnum } from "$components/github/ViewTypes";
  import { themes } from "$lib/store/theme";

  let viewType = ViewTypeEnum.Grid;

  // Add a prop to control whether to show only private repos
  export let privateOnly = true;

  // Handler for view type change events from child components
  function handleViewTypeChange(event) {
    viewType = event.detail.viewType;
  }
</script>

<div class="container mx-auto px-4 py-8">
  <div class="mb-6 flex items-center gap-4">
    <img
      src={themes.default.logo.src}
      alt={themes.default.logo.alt}
      class="h-12 w-auto"
    />
    <div>
      <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
        GitHub Integration
      </h1>
      <p class="text-gray-600 dark:text-gray-300">
        Connect your GitHub repositories via GitHub App installations
      </p>
    </div>
  </div>

  <GitHubAppViewToggle bind:viewType />

  {#if viewType === ViewTypeEnum.List}
    <GitHubRepositoryList
      {privateOnly}
      on:viewTypeChange={handleViewTypeChange}
    />
  {:else if viewType === ViewTypeEnum.Grid}
    <GitHubRepositoryGrid
      {privateOnly}
      on:viewTypeChange={handleViewTypeChange}
    />
  {:else if viewType === ViewTypeEnum.Installations}
    <GitHubInstallations />
  {/if}

  <div class="mt-12 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
    <h2 class="text-xl font-medium text-gray-900 dark:text-white mb-4">
      What is GitHub App?
    </h2>
    <p class="text-gray-600 dark:text-gray-300 mb-4">
      GitHub Apps are a more secure and flexible way to integrate with GitHub
      repositories. They can be installed on personal or organization accounts
      and can access specific repositories with granular permissions.
    </p>

    <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2 mt-6">
      Benefits of GitHub Apps
    </h3>
    <ul
      class="list-disc list-inside text-gray-600 dark:text-gray-300 space-y-2"
    >
      <li>More secure authentication via OAuth 2.0</li>
      <li>Fine-grained permissions to access only what's needed</li>
      <li>Can be installed on specific repositories</li>
      <li>Ability to subscribe to webhook events</li>
      <li>Higher rate limits compared to OAuth apps</li>
    </ul>

    <div class="mt-8">
      <a
        href="/github/installations"
        class="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300 font-medium"
      >
        View your current installations <span aria-hidden="true">→</span>
      </a>
    </div>
  </div>
</div>
