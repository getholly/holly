<script lang="ts">
  import { Alert, Spinner } from "flowbite-svelte";
  import { get } from "svelte/store";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";
  import { currentMission } from "$lib/store/mission/mission.store";
  import { repositoriesStore } from "$lib/store/github/repositories.store";
  import { getMission, setRepositories } from "$lib/apis/mission/api.mission";
  import {
    transformMissionReposToGitMultiSelect,
    transformGitMultiSelectToSyncFormat,
    areRepoSelectionsEqual,
    type RepoSelection,
  } from "$lib/utils/missionRepoTransforms";

  // GitHub Repository section state
  let gitMultiSelectRef: GitMultiSelect;
  let initialSelections: RepoSelection[] = [];
  let isLoadingRepos = false;
  let syncError: string | null = null;
  let isSyncing = false;

  // Reactive statements
  // Update initial selections when currentMission changes
  $: if ($currentMission?.repositories) {
    console.log(
      "SettingsModalGithub: Current mission changed, updating repo selections",
      $currentMission.title,
      $currentMission.repositories,
    );
    updateInitialSelections($currentMission.repositories);
  } else if ($currentMission === null) {
    console.log("SettingsModalGithub: Mission cleared, resetting selections");
    initialSelections = [];
  }

  // Handle repository store loading - only fetch if not already fetched
  $: if (
    !$repositoriesStore.loading &&
    $repositoriesStore.repositories.length === 0 &&
    !$repositoriesStore.lastFetched
  ) {
    console.log(
      "SettingsModalGithub: Repository store is empty, fetching repositories",
    );
    repositoriesStore.fetchRepositories(true).catch((err) => {
      console.error("Failed to load repositories in SettingsModalGithub:", err);
    });
  }

  function updateInitialSelections(missionRepos: any[]) {
    console.log(
      "SettingsModalGithub: updateInitialSelections called with",
      missionRepos,
    );

    if (!missionRepos || missionRepos.length === 0) {
      console.log("SettingsModalGithub: No mission repos, clearing selections");
      initialSelections = [];
      return;
    }

    if ($repositoriesStore.loading) {
      console.log(
        "SettingsModalGithub: Repository store still loading, setting loading flag",
      );
      isLoadingRepos = true;
      return;
    }

    console.log(
      "SettingsModalGithub: Repository store loaded, transforming mission repos",
    );
    isLoadingRepos = false;

    const newInitialSelections =
      transformMissionReposToGitMultiSelect(missionRepos);
    console.log(
      "SettingsModalGithub: Transformed selections:",
      newInitialSelections,
    );
    initialSelections = newInitialSelections;
  }

  async function handleRepoSelectionChange(event: CustomEvent) {
    const newSelections = event.detail;

    if (!$currentMission) {
      console.warn(
        "No current mission selected, cannot sync repository changes",
      );
      return;
    }

    console.log(
      "SettingsModalGithub: Syncing repository changes to mission",
      $currentMission.id,
      newSelections,
    );

    isSyncing = true;
    syncError = null;

    try {
      const repositories = get(repositoriesStore).repositories;
      const repoData = newSelections.map((selection) => {
        const repo = repositories.find(
          (r) => r.full_name === selection.repoFullName,
        );
        if (!repo) {
          throw new Error(
            `Repository ${selection.repoFullName} not found in store`,
          );
        }
        return {
          github_id: repo.id,
          branch_name: selection.branch || "main",
        };
      });

      const response = await setRepositories($currentMission.id, {
        repos: repoData,
      });

      if (response.success) {
        console.log(
          "SettingsModalGithub: Repository sync successful",
          response.message,
        );
        const updatedMission = await getMission($currentMission.id);
        currentMission.set(updatedMission);
      } else {
        console.error(
          "SettingsModalGithub: Repository sync failed",
          response.message,
        );
        syncError = response.message;
      }
    } catch (error) {
      console.error("SettingsModalGithub: Error syncing repositories", error);
      syncError =
        error instanceof Error ? error.message : "Unknown error occurred";
    } finally {
      isSyncing = false;
    }
  }
</script>

<div class="space-y-6">
  <div>
    <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
      GitHub Repository
    </h4>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Configure which GitHub repositories are connected to your current mission.
    </p>
  </div>

  <!-- Loading state -->
  {#if isLoadingRepos || $repositoriesStore.loading}
    <div class="flex items-center gap-2 mb-4">
      <Spinner size="4" />
      <span class="text-sm text-gray-500">Loading repositories...</span>
    </div>
  {/if}

  <!-- Sync status indicators -->
  {#if isSyncing}
    <div
      class="flex items-center gap-2 mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded"
    >
      <Spinner size="4" />
      <span class="text-sm text-blue-600 dark:text-blue-400"
        >Syncing repository changes...</span
      >
    </div>
  {/if}

  <!-- Sync error -->
  {#if syncError}
    <Alert color="red" class="mb-4">
      <span class="font-medium">Sync Error:</span>
      {syncError}
    </Alert>
  {/if}

  <!-- Mission context info -->
  {#if $currentMission}
    <div class="mb-4 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
      <p class="font-medium text-gray-700 dark:text-gray-300">
        Mission: {$currentMission.title}
      </p>
      <p class="text-gray-500">
        {$currentMission.repositories?.length || 0} repositories connected
      </p>
    </div>
  {:else}
    <div class="mb-4 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
      <p class="text-yellow-600 dark:text-yellow-400">
        No mission selected. Repository changes will not be saved.
      </p>
    </div>
  {/if}

  <!-- GitMultiSelect with 2-way binding -->
  <GitMultiSelect
    bind:this={gitMultiSelectRef}
    {initialSelections}
    privateOnly={true}
    on:selectionchange={handleRepoSelectionChange}
  />
</div>
