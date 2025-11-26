<script lang="ts">
  import { onMount, createEventDispatcher, tick } from "svelte";
  import {
    Checkbox,
    Listgroup,
    ListgroupItem,
    Select,
    Spinner,
    Input,
    Label,
    Toggle,
  } from "flowbite-svelte";
  import type { GitHubBranch, RepoSelection } from "$lib/types/githubTypes";
  import type { GitHubRepository } from "$lib/types/github/repository";
  import { repositoriesStore } from "$lib/store/github/repositories.store";
  import { getBranches } from "$lib/apis/git/api.git";
  import type { RepositoryBranchesRequest } from "holly-api";

  // Option to control whether to show only private repos
  export let privateOnly = false;
  // Allow passing in initial selections
  export let initialSelections: RepoSelection[] = [];

  const dispatch = createEventDispatcher();
  let selectedRepos = new Map<string, RepoSelection>();
  let searchTerm = "";
  let isInternalUpdate = false;
  let lastInitialSelections: RepoSelection[] = [];

  // Deep equality check for RepoSelection arrays
  function areSelectionsEqual(a: RepoSelection[], b: RepoSelection[]): boolean {
    if (a.length !== b.length) return false;

    for (let i = 0; i < a.length; i++) {
      const selA = a[i];
      const selB = b[i];

      if (
        selA.repo.full_name !== selB.repo.full_name ||
        selA.selectedBranch !== selB.selectedBranch
      ) {
        return false;
      }
    }
    return true;
  }

  // Handle initialSelections changes with proper equality checking
  $: handleInitialSelectionsChange(initialSelections);

  async function handleInitialSelectionsChange(selections: RepoSelection[]) {
    // Skip if no real change (deep equality check)
    if (areSelectionsEqual(selections, lastInitialSelections)) {
      return;
    }

    console.log(
      "GitMultiSelect: Processing initialSelections change",
      selections.length,
    );

    // Update last known state
    lastInitialSelections = [...selections];

    // Set flag to prevent dispatching during update
    isInternalUpdate = true;

    // Create new map from selections
    const newSelectedRepos = new Map<string, RepoSelection>();

    for (const selection of selections) {
      newSelectedRepos.set(selection.repo.full_name, {
        ...selection,
        selectedBranch: selection.selectedBranch || "main",
      });
    }

    selectedRepos = newSelectedRepos;

    // Wait for DOM updates to complete
    await tick();

    // Clear flag after update
    isInternalUpdate = false;

    console.log(
      "GitMultiSelect: Updated selectedRepos from initialSelections",
      selectedRepos.size,
    );
  }

  // Computed selection array - using $ prefix as per conventions
  $: finalSelection = Array.from(selectedRepos.values());

  // Dispatch changes only when not during internal updates
  $: if (!isInternalUpdate && finalSelection.length >= 0) {
    console.log(
      "GitMultiSelect: Dispatching selection change",
      finalSelection.length,
    );
    dispatch("selectionchange", finalSelection);
  }

  // Filter repositories - using $ prefix as per conventions
  $: filteredRepositories = $repositoriesStore.repositories.filter((repo) =>
    repo.full_name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  onMount(async () => {
    // Initialize with any passed selections
    if (initialSelections.length > 0) {
      await handleInitialSelectionsChange(initialSelections);
    }

    // Load repositories if needed
    if (
      $repositoriesStore.repositories.length === 0 &&
      !$repositoriesStore.loading
    ) {
      repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
        console.error("Failed to load repositories:", err);
      });
    }
  });

  async function fetchBranches(repoFullName: string) {
    const currentSelection = selectedRepos.get(repoFullName);
    if (!currentSelection) return;

    currentSelection.isLoadingBranches = true;
    currentSelection.errorBranches = undefined;
    selectedRepos = new Map(selectedRepos.set(repoFullName, currentSelection));

    try {
      // Parse repoFullName to get owner and name
      const [repo_owner, repo_name] = repoFullName.split("/");
      if (!repo_owner || !repo_name) {
        throw new Error("Invalid repository full name format");
      }

      // Call the getBranches API
      const request: RepositoryBranchesRequest = {
        repo_owner,
        repo_name,
      };

      const branchesResponse = await getBranches(request);

      if (!branchesResponse.success) {
        throw new Error(branchesResponse.message || "Failed to fetch branches");
      }

      // Transform string array to GitHubBranch objects
      const branches: GitHubBranch[] = branchesResponse.branches.map(
        (branchName) => ({
          name: branchName,
          commit: { sha: "", url: "" },
          protected: false,
        }),
      );

      currentSelection.branches = branches;

      // Set default branch if not already selected
      if (!currentSelection.selectedBranch) {
        const defaultBranchName =
          branchesResponse.current_branch || branches[0]?.name || null;
        currentSelection.selectedBranch = defaultBranchName;
      }
    } catch (err: any) {
      console.error(`Error fetching branches for ${repoFullName}:`, err);
      currentSelection.errorBranches =
        err.message || `Failed to fetch branches`;
    } finally {
      currentSelection.isLoadingBranches = false;
      selectedRepos = new Map(
        selectedRepos.set(repoFullName, currentSelection),
      );
    }
  }

  function handleCheckboxChange(repo: GitHubRepository, event: Event) {
    const input = event.target as HTMLInputElement;
    if (input && typeof input.checked === "boolean") {
      handleRepoToggle(repo, input.checked);
    }
  }

  async function handleRepoToggle(repo: GitHubRepository, isSelected: boolean) {
    console.log(
      "GitMultiSelect: User toggled repo",
      repo.full_name,
      "to",
      isSelected,
    );

    // Set flag to indicate user-initiated change
    isInternalUpdate = true;

    if (isSelected) {
      if (!selectedRepos.has(repo.full_name)) {
        const newSelection: RepoSelection = {
          repo: repo,
          selectedBranch: null,
          branches: [],
          isLoadingBranches: true,
          errorBranches: undefined,
        };
        selectedRepos = new Map(
          selectedRepos.set(repo.full_name, newSelection),
        );

        // Wait for state update then fetch branches
        await tick();
        await fetchBranches(repo.full_name);
      }
    } else {
      selectedRepos.delete(repo.full_name);
      selectedRepos = new Map(selectedRepos);
    }

    // Wait for updates to complete
    await tick();

    // Clear flag to allow dispatching
    isInternalUpdate = false;
  }

  async function handleBranchChange(repoFullName: string, event: Event) {
    const target = event.target as HTMLSelectElement;
    const currentSelection = selectedRepos.get(repoFullName);
    if (currentSelection) {
      console.log(
        "GitMultiSelect: User changed branch for",
        repoFullName,
        "to",
        target.value,
      );

      isInternalUpdate = true;
      currentSelection.selectedBranch = target.value || null;
      selectedRepos = new Map(
        selectedRepos.set(repoFullName, currentSelection),
      );

      await tick();
      isInternalUpdate = false;
    }
  }

  // Handler for refresh button
  function refreshRepositories() {
    repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
      console.error("Failed to refresh repositories:", err);
    });
  }

  // Handler for private only toggle
  async function handlePrivateToggle() {
    // Set flag during major state change
    isInternalUpdate = true;

    // Clear current selections since repo list will change
    selectedRepos.clear();
    selectedRepos = new Map(selectedRepos);

    // Wait for state to update
    await tick();

    // Fetch repositories with new filter
    repositoriesStore.fetchRepositories(privateOnly).catch((err) => {
      console.error("Failed to refresh repositories with new filter:", err);
    });

    // Clear flag
    isInternalUpdate = false;
  }

  // Export the selection for external access
  export function getSelections() {
    return Array.from(selectedRepos.values());
  }
</script>

<div class="space-y-4">
  <Label class="space-y-2">
    <span>Filter Repositories</span>
    <Input type="text" placeholder="Search..." bind:value={searchTerm} />
  </Label>

  <div class="flex items-center justify-between">
    <div class="flex items-center space-x-3">
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300"
        >All Repos</span
      >
      <Toggle bind:checked={privateOnly} on:change={handlePrivateToggle} />
      <span class="text-sm font-medium text-gray-700 dark:text-gray-300"
        >Private Only</span
      >
    </div>
  </div>

  {#if $repositoriesStore.loading}
    <div class="flex items-center gap-2">
      <Spinner size="4" />
      Loading repositories...
    </div>
  {:else if $repositoriesStore.error}
    <p class="text-red-600">Error: {$repositoriesStore.error}</p>
    <button
      on:click={refreshRepositories}
      class="px-3 py-1.5 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
    >
      Try Again
    </button>
  {:else}
    <div class="flex justify-between items-center mb-2">
      <p class="text-sm text-gray-500 dark:text-gray-400">
        {filteredRepositories.length}
        {privateOnly ? "private" : ""} repositories found
      </p>
      <button
        on:click={refreshRepositories}
        class="px-2 py-1 border border-transparent text-xs font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        disabled={$repositoriesStore.loading}
      >
        {$repositoriesStore.loading ? "Refreshing..." : "Refresh"}
      </button>
    </div>
    <Listgroup class="w-full">
      {#each filteredRepositories as repo (repo.id)}
        <ListgroupItem class="p-2">
          <Checkbox
            class="p-0 m-0 mr-2"
            checked={selectedRepos.has(repo.full_name)}
            on:change={(e) => handleCheckboxChange(repo, e)}
          >
            {repo.full_name}
            {repo.private ? "(Private)" : ""}
          </Checkbox>
        </ListgroupItem>
      {:else}
        <ListgroupItem class="p-2 text-gray-500"
          >No repositories found{searchTerm ? " matching filter" : ""}.
        </ListgroupItem>
      {/each}
    </Listgroup>
  {/if}

  <hr />
  <h3 class="text-lg font-semibold">Selected Repositories & Branches:</h3>

  {#if selectedRepos.size === 0}
    <p class="text-gray-500">No repositories selected.</p>
  {:else}
    <div class="space-y-3">
      {#each Array.from(selectedRepos.entries()) as [fullName, selection] (fullName)}
        <div class="border p-3 rounded-lg">
          <strong class="block mb-2">{selection.repo.full_name}</strong>
          {#if selection.isLoadingBranches}
            <div class="flex items-center gap-2 text-sm text-gray-500">
              <Spinner size="4" />
              Loading branches...
            </div>
          {:else if selection.errorBranches}
            <p class="text-red-600 text-sm">
              Error loading branches: {selection.errorBranches}
            </p>
          {:else if selection.branches.length === 0}
            <p class="text-sm text-gray-500">No branches found.</p>
          {:else}
            <Label class="space-y-1 w-full">
              <span>Select Branch</span>
              <Select
                class="w-full"
                items={[
                  { value: "", name: "-- Select Branch --" },
                  ...selection.branches.map((b) => ({
                    value: b.name,
                    name: b.name,
                  })),
                ]}
                value={selection.selectedBranch ?? ""}
                on:change={(e) => handleBranchChange(fullName, e)}
              />
            </Label>
          {/if}
        </div>
      {/each}
    </div>
  {/if}
</div>
