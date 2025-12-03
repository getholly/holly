<script lang="ts">
  import {
    Button,
    Modal,
    Label,
    Input,
    Textarea,
    Tabs,
    TabItem,
  } from "flowbite-svelte";
  import { createEventDispatcher } from "svelte";
  import {
    updateMission,
    addRepositories,
    removeRepositories,
  } from "$lib/apis/mission/api.mission";
  import type {
    MissionDetail,
    MissionUpdate,
    MissionRepositoryAddSchema,
    MissionRepositoryRemoveSchema,
    MissionRepositoryResponseSchema,
    MissionRepoAdd,
  } from "holly-api";
  import type { RepoSelection } from "$lib/types/githubTypes";
  import {
    FloppyDiskAltOutline,
    TrashBinOutline,
  } from "flowbite-svelte-icons";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";

  export let open = false;
  export let mission: MissionDetail | null = null;

  const dispatch = createEventDispatcher();

  let error = "";
  let success = "";
  let activeTab = 0; // 0 = Details, 1 = Repositories

  // Repository management
  let selectedRepos: RepoSelection[] = [];
  let missionRepos: MissionRepositoryResponseSchema[] = [];

  // Form fields for editing
  let editForm: MissionUpdate = {
    title: "",
    description: "",
    branch_name: "",
  };

  // React to mission changes
  $: if (mission && open) {
    editForm = {
      title: mission.title,
      description: mission.description || "",
      branch_name: mission.branch_name,
    };
    missionRepos = mission.repositories || [];
    error = "";
    success = "";
  }

  async function handleUpdateMission() {
    if (!mission) {
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
      await updateMission(mission.id, editForm);

      // Show success message
      success = "Mission updated successfully";

      dispatch("update");

      // Close modal only if we're on the Details tab
      if (activeTab === 0) {
        close();
      }
    } catch (err) {
      error = "Failed to update mission. Please try again.";
      console.error("Error updating mission:", err);
    }
  }

  function close() {
    open = false;
    dispatch("close");
  }

  // Handle repository selection changes
  function handleRepoSelect(event: CustomEvent<RepoSelection[]>) {
    selectedRepos = event.detail;
  }

  // Save repositories to mission
  async function handleSaveRepositories() {
    if (!mission || !selectedRepos || selectedRepos.length === 0) {
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

      // Add the repositories to the mission
      await addRepositories(mission.id, repoData);

      // Show success message
      success = "Repositories added to mission successfully";

      dispatch("update");
      
      // Need to refresh local repos list too, ideally we get it from parent update but 
      // for immediate feedback we might want to reload mission data or wait for parent.
      // The parent will refresh the list.
    } catch (err) {
      error = "Failed to add repositories to mission. Please try again.";
      console.error(
        "Error adding repositories to mission with ID",
        mission.id,
        ":",
        err,
      );
    }
  }

  // Remove a repository from the mission
  async function handleRemoveRepository(repoId: number) {
    if (!mission || !repoId) {
      return;
    }

    try {
      // Prepare repository data for API - must match MissionRepositoryRemoveSchema
      const repoData: MissionRepositoryRemoveSchema = {
        repository_ids: [repoId],
      };

      // Remove the repository from the mission
      if (repoData.repository_ids.length > 0) {
        await removeRepositories(mission.id, repoData);
      }

      // Show success message
      success = "Repository removed from mission successfully";
      
      // Optimistically update local list
      missionRepos = missionRepos.filter(r => r.id !== repoId);
      
      dispatch("update");
    } catch (err) {
      error = "Failed to remove repository from mission. Please try again.";
      console.error("Error removing repository:", err);
    }
  }
</script>

<Modal
  bind:open
  size="xl"
  title="Edit Mission"
  autoclose={false}
  on:close={close}
>
  <Tabs>
    <TabItem title="Details" open={activeTab === 0} on:click={() => activeTab = 0}>
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
          <Button color="alternative" on:click={close}>Cancel</Button>
          <Button type="submit" color="blue">
            <FloppyDiskAltOutline class="w-4 h-4 mr-1" />
            Save Changes
          </Button>
        </div>
      </form>
    </TabItem>

    <TabItem title="Repositories" open={activeTab === 1} on:click={() => activeTab = 1}>
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



