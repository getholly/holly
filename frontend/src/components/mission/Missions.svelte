<script lang="ts">
  import {
    Select,
    Button,
    Modal,
    Label,
    Input,
    Textarea,
    Tabs,
    TabItem,
  } from "flowbite-svelte";
  import { onMount } from "svelte";
  import { currentMission } from "$lib/store/mission/mission.store";
  import {
    getMissions,
    getMission,
    updateMission,
    addRepositories,
    removeRepositories,
    deleteMission,
  } from "$lib/apis/mission/api.mission";
  import type {
    MissionSummary,
    MissionUpdate,
    MissionRepositoryAddSchema,
    MissionRepositoryRemoveSchema,
    MissionRepositoryResponseSchema,
    MissionRepoAdd,
  } from "holly-api";
  import type { RepoSelection } from "$lib/types/githubTypes";
  import {
    CogOutline,
    FloppyDiskAltOutline,
    TrashBinOutline,
    InfoCircleOutline,
  } from "flowbite-svelte-icons";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";

  let missions: MissionSummary[] = [];
  let selectedMissionId = "";
  let isLoading = true;
  let error = "";
  let success = "";
  let showEditModal = false;
  let showDeleteConfirmModal = false;
  let activeTab = 0; // 0 = Details, 1 = Repositories
  let showTooltip = false;

  // Repository management
  let selectedRepos: RepoSelection[] = [];
  let missionRepos: MissionRepositoryResponseSchema[] = [];

  // Form fields for editing
  let editForm: MissionUpdate = {
    title: "",
    description: "",
    branch_name: "",
  };

  onMount(async () => {
    try {
      missions = await getMissions();
      isLoading = false;

      // Set the first mission as selected by default if available
      if (missions.length > 0) {
        selectedMissionId = missions[0].id;
        await selectMission(selectedMissionId);
      }
    } catch (err) {
      isLoading = false;
      error = "Failed to load missions. Please try again.";
      console.error("Error loading missions:", err);
    }
  });

  async function selectMission(missionId: string) {
    if (!missionId) {
      currentMission.set(null);
      return;
    }

    try {
      const missionDetail = await getMission(missionId);
      currentMission.set(missionDetail);
      console.log(`Selected mission:`, missionDetail);

      // Extract repositories from mission for display
      if (missionDetail && missionDetail.repositories) {
        missionRepos = missionDetail.repositories;
      } else {
        missionRepos = [];
      }
    } catch (err) {
      error = `Failed to load mission details for ID: ${missionId}`;
      console.error(error, err);
    }
  }

  function handleMissionChange() {
    selectMission(selectedMissionId);
  }

  function openEditModal() {
    // Reset messages
    error = "";
    success = "";

    // Get the current mission data
    const currentMissionValue = $currentMission;
    if (currentMissionValue) {
      editForm = {
        title: currentMissionValue.title,
        description: currentMissionValue.description || "",
        branch_name: currentMissionValue.branch_name,
      };
      missionRepos = currentMissionValue.repositories || [];
      showEditModal = true;
      activeTab = 0; // Default to Details tab
    } else {
      error = "No mission selected";
    }
  }

  async function handleUpdateMission() {
    if (!selectedMissionId) {
      error = "No mission selected";
      return;
    }

    try {
      // Validate form inputs
      if (!editForm.title) {
        error = "Title is required";
        return;
      }

      // Update the mission
      await updateMission(selectedMissionId, editForm);

      // Refresh mission data
      await selectMission(selectedMissionId);

      // Show success message
      success = "Mission updated successfully";

      // Close modal only if we're on the Details tab
      if (activeTab === 0) {
        showEditModal = false;
      }

      // Update the mission list to reflect the changes
      missions = await getMissions();
    } catch (err) {
      error = "Failed to update mission. Please try again.";
      console.error("Error updating mission:", err);
    }
  }

  // Handle repository selection changes
  function handleRepoSelect(event: CustomEvent<RepoSelection[]>) {
    selectedRepos = event.detail;
  }

  // Save repositories to mission
  async function handleSaveRepositories() {
    if (!selectedMissionId || !selectedRepos || selectedRepos.length === 0) {
      error = "No repositories selected";
      return;
    }

    try {
      // Prepare repository data for API - must match MissionRepositoryAddSchema
      const repoData: MissionRepositoryAddSchema = {
        repos: selectedRepos
          .map((repo) => ({
            github_id: repo.repo?.id,
            branch_name: repo.selectedBranch || "main",
          }))
          .filter((r): r is MissionRepoAdd => r.github_id !== undefined),
      };

      console.log(
        "Adding repositories to mission with ID",
        selectedMissionId,
        ":",
        repoData,
      );

      // Add the repositories to the mission
      await addRepositories(selectedMissionId, repoData);

      // Refresh mission data
      await selectMission(selectedMissionId);

      // Show success message
      success = "Repositories added to mission successfully";

      // Don't close the modal so user can continue working with repositories
    } catch (err) {
      error = "Failed to add repositories to mission. Please try again.";
      console.error(
        "Error adding repositories to mission with ID",
        selectedMissionId,
        ":",
        err,
      );
    }
  }

  // Remove a repository from the mission
  async function handleRemoveRepository(repoId: number) {
    if (!selectedMissionId || !repoId) {
      return;
    }

    try {
      // Prepare repository data for API - must match MissionRepositoryRemoveSchema
      const repoData: MissionRepositoryRemoveSchema = {
        repository_ids: [repoId],
      };

      // Remove the repository from the mission
      if (repoData.repository_ids.length > 0) {
        await removeRepositories(selectedMissionId, repoData);
      }

      // Refresh mission data
      await selectMission(selectedMissionId);

      // Show success message
      success = "Repository removed from mission successfully";
    } catch (err) {
      error = "Failed to remove repository from mission. Please try again.";
      console.error("Error removing repository:", err);
    }
  }

  function openDeleteConfirmModal() {
    if ($currentMission) {
      showDeleteConfirmModal = true;
    } else {
      error = "No mission selected";
    }
  }

  async function handleDeleteMission() {
    if (!selectedMissionId) {
      error = "No mission selected";
      return;
    }

    try {
      const response = await deleteMission(selectedMissionId);

      if (!response.success) {
        error = response.message || "Failed to delete mission";
        return;
      }

      // Success - close modal and refresh missions
      showDeleteConfirmModal = false;
      success = "Mission deleted successfully";
      error = "";

      // Refresh mission list
      missions = await getMissions();

      // Clear current mission and selected ID
      currentMission.set(null);
      selectedMissionId = "";

      // Clear any selected mission after 3 seconds
      setTimeout(() => {
        success = "";
      }, 3000);
    } catch (err) {
      error =
        err instanceof Error
          ? err.message
          : "Failed to delete mission. Please try again.";
      console.error("Error deleting mission:", err);
    }
  }

  function toggleTooltip() {
    showTooltip = !showTooltip;
  }
</script>

<!-- Horizontal mission bar -->
<div
  class="w-full bg-gray-100 dark:bg-gray-800 shadow-md border-b border-gray-300 dark:border-gray-700"
>
  {#if isLoading}
    <div class="flex justify-center items-center py-2">
      <div
        class="animate-spin h-5 w-5 mr-3 border-t-2 border-b-2 border-blue-500 rounded-full"
      ></div>
      <p>Loading missions...</p>
    </div>
  {:else if error}
    <div class="text-sm text-red-700 px-3 py-1 rounded-sm" role="alert">
      <span class="font-medium">Error!</span>
      {error}
    </div>
  {:else if success}
    <div class="text-sm text-green-700 px-3 py-1 rounded-sm" role="alert">
      <span class="font-medium">Success!</span>
      {success}
    </div>
  {:else if missions.length === 0}
    <div class="text-sm text-gray-500 py-2 px-4">
      No missions available. Create a new mission to get started.
    </div>
  {:else}
    <div class="flex items-center gap-4 py-2 px-4">
      <!-- Mission selector -->
      <div class="w-64">
        <Select
          class="m-0"
          size="sm"
          bind:value={selectedMissionId}
          on:change={handleMissionChange}
        >
          {#each missions as mission}
            <option value={mission.id}>
              {mission.title} ({mission.state})
            </option>
          {/each}
        </Select>
      </div>

      <!-- Current mission info (only shown when a mission is selected) -->
      {#if $currentMission}
        <div class="flex-grow flex flex-wrap items-center gap-3 text-sm">
          <div
            class="font-medium"
            title={$currentMission.description || "No description"}
          >
            {$currentMission.title}
          </div>
          <div class="text-gray-500">
            Branch: {$currentMission.branch_name || "Default"}
          </div>
          <div class="text-gray-500">
            Repos: {$currentMission.repositories?.length || 0}
          </div>
          <div class="text-gray-500">
            State: <span
              class={$currentMission.state === "active"
                ? "text-green-500"
                : "text-yellow-500"}
            >
              {$currentMission.state}
            </span>
          </div>
          <div class="text-gray-500">
            Container: <span
              class={$currentMission.container_id
                ? "text-green-500"
                : "text-red-500"}
            >
              {$currentMission.container_id ? "Running" : "Not started"}
            </span>
          </div>

          <!-- Info button to show description tooltip -->
          {#if $currentMission.description}
            <Button
              size="xs"
              color="light"
              class="p-1"
              on:click={toggleTooltip}
            >
              <InfoCircleOutline class="w-4 h-4" />
            </Button>
            {#if showTooltip}
              <div
                class="absolute z-10 bg-gray-100 dark:bg-gray-700 p-2 rounded shadow-lg mt-16"
              >
                <p class="text-sm">{$currentMission.description}</p>
              </div>
            {/if}
          {/if}
        </div>
      {/if}

      <!-- Action buttons -->
      <div class="flex gap-2">
        <Button
          size="sm"
          color="light"
          class="whitespace-nowrap"
          on:click={openEditModal}
        >
          <CogOutline class="w-4 h-4 mr-1" />
          Edit Mission
        </Button>
        <Button
          size="sm"
          color="red"
          class="whitespace-nowrap"
          on:click={openDeleteConfirmModal}
        >
          <TrashBinOutline class="w-4 h-4 mr-1" />
          Delete Mission
        </Button>
      </div>
    </div>
  {/if}
</div>

<!-- Edit Mission Modal with Tabs -->
<Modal
  bind:open={showEditModal}
  size="xl"
  title="Edit Mission"
  autoclose={false}
>
  <Tabs>
    <TabItem title="Details" open={activeTab === 0}>
      <form on:submit|preventDefault={handleUpdateMission} class="space-y-4">
        <div>
          <Label for="title" class="mb-2">Title</Label>
          <Input
            id="title"
            required
            bind:value={editForm.title}
            placeholder="Mission Title"
          />
        </div>

        <div>
          <Label for="description" class="mb-2">Description</Label>
          <Textarea
            id="description"
            rows={4}
            bind:value={editForm.description}
            placeholder="Mission Description"
          />
        </div>

        <div>
          <Label for="branch_name" class="mb-2">Branch Name</Label>
          <Input
            id="branch_name"
            bind:value={editForm.branch_name}
            placeholder="Branch Name"
          />
        </div>

        <div class="flex justify-end gap-2">
          <Button color="alternative" on:click={() => (showEditModal = false)}
            >Cancel</Button
          >
          <Button type="submit" color="blue">
            <FloppyDiskAltOutline class="w-4 h-4 mr-1" />
            Save Changes
          </Button>
        </div>
      </form>
    </TabItem>

    <TabItem title="Repositories" open={activeTab === 1}>
      {#if error}
        <div
          class="text-sm text-red-700 bg-red-100 px-3 py-1 rounded-sm mb-4"
          role="alert"
        >
          <span class="font-medium">Error!</span>
          {error}
        </div>
      {/if}

      {#if success}
        <div
          class="text-sm text-green-700 bg-green-100 px-3 py-1 rounded-sm mb-4"
          role="alert"
        >
          <span class="font-medium">Success!</span>
          {success}
        </div>
      {/if}
      <div class="space-y-4">
        <div>
          <h3 class="text-lg font-semibold mb-2">Current Repositories</h3>
          {#if missionRepos && missionRepos.length > 0}
            <div class="space-y-2">
              {#each missionRepos as repo}
                <div
                  class="flex justify-between items-center p-3 border rounded"
                >
                  <div>
                    <p class="font-medium">{repo.name}</p>
                    <p class="text-sm text-gray-500">{repo.owner}</p>
                  </div>
                  <Button
                    size="xs"
                    color="red"
                    on:click={() => handleRemoveRepository(repo.id)}
                  >
                    <TrashBinOutline class="w-3 h-3" />
                  </Button>
                </div>
              {/each}
            </div>
          {:else}
            <p class="text-gray-500">
              No repositories connected to this mission.
            </p>
          {/if}
        </div>

        <hr />

        <div>
          <h3 class="text-lg font-semibold mb-4">Add Repositories</h3>
          <GitMultiSelect on:selectionchange={handleRepoSelect} />

          <div class="flex justify-end mt-4">
            <Button
              color="blue"
              on:click={handleSaveRepositories}
              disabled={!selectedRepos.length}
            >
              Add Repositories to Mission
            </Button>
          </div>
        </div>
      </div>
    </TabItem>
  </Tabs>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal
  bind:open={showDeleteConfirmModal}
  size="md"
  title="Delete Mission"
  autoclose={false}
>
  <div class="space-y-4">
    <p class="text-gray-700 dark:text-gray-300">
      Are you sure you want to delete this mission? This action cannot be
      undone.
    </p>

    {#if $currentMission}
      <div
        class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3"
      >
        <p class="text-sm text-red-800 dark:text-red-200">
          <strong>Mission:</strong>
          {$currentMission.title}
        </p>
      </div>
    {/if}

    <div class="flex justify-end gap-2 pt-4">
      <Button
        color="alternative"
        on:click={() => (showDeleteConfirmModal = false)}>Cancel</Button
      >
      <Button color="red" on:click={handleDeleteMission}>
        <TrashBinOutline class="w-4 h-4 mr-1" />
        Delete Mission
      </Button>
    </div>
  </div>
</Modal>
