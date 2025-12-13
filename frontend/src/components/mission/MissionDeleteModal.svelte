<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import { createEventDispatcher } from "svelte";
  import { deleteMission } from "$lib/apis/mission/api.mission";
  import type { MissionDetail, MissionSummary } from "holly-api";
  import { TrashBinOutline } from "flowbite-svelte-icons";

  export let open = false;
  // Accept either Detail or Summary as both have id and title
  export let mission: MissionDetail | MissionSummary | null = null;

  const dispatch = createEventDispatcher();
  let error = "";

  async function handleDeleteMission() {
    if (!mission) {
      error = "No mission selected";
      return;
    }

    try {
      const response = await deleteMission(mission.id);

      if (!response.success) {
        error = response.message || "Failed to delete mission";
        return;
      }

      dispatch("delete");
      close();
    } catch (err) {
      error =
        err instanceof Error
          ? err.message
          : "Failed to delete mission. Please try again.";
      console.error("Error deleting mission:", err);
    }
  }

  function close() {
    open = false;
    error = "";
    dispatch("close");
  }
</script>

<Modal
  bind:open
  size="md"
  title="Delete Mission"
  autoclose={false}
  on:close={close}
>
  <div class="space-y-4">
    <p class="text-gray-700 dark:text-gray-300">
      Are you sure you want to delete this mission? This action cannot be
      undone.
    </p>

    {#if error}
      <div class="text-sm text-red-700 bg-red-100 px-3 py-1 rounded-sm" role="alert">
        <span class="font-medium">Error!</span>
        {error}
      </div>
    {/if}

    {#if mission}
      <div
        class="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded p-3"
      >
        <p class="text-sm text-red-800 dark:text-red-200">
          <strong>Mission:</strong>
          {mission.title}
        </p>
      </div>
    {/if}

    <div class="flex justify-end gap-2 pt-4">
      <Button color="alternative" on:click={close}>Cancel</Button>
      <Button color="red" on:click={handleDeleteMission}>
        <TrashBinOutline class="w-4 h-4 mr-1" />
        Delete Mission
      </Button>
    </div>
  </div>
</Modal>
