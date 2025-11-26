<script lang="ts">
  import { Alert, Spinner } from "flowbite-svelte";
  import ToolSelector from "$components/staticdata/ToolSelector.svelte";
  import { currentMission } from "$lib/store/mission/mission.store";
  import { getMission, setTools } from "$lib/apis/mission/api.mission";

  let selectedTools: number[] = [];
  let toolSyncError: string | null = null;
  let isToolSyncing = false;

  async function handleToolSelectionChange(event: CustomEvent) {
    const newSelectedTools = event.detail.selectedTools;

    if (!$currentMission) {
      console.warn("No current mission selected, cannot sync tool changes");
      return;
    }

    console.log(
      "SettingsModal: Syncing tool changes to mission",
      $currentMission.id,
      newSelectedTools,
    );

    isToolSyncing = true;
    toolSyncError = null;

    try {
      const response = await setTools($currentMission.id, {
        tool_ids: newSelectedTools,
      });

      if (response.success) {
        console.log("SettingsModal: Tool sync successful", response.message);
        const updatedMission = await getMission($currentMission.id);
        currentMission.set(updatedMission);
      } else {
        console.error("SettingsModal: Tool sync failed", response.message);
        toolSyncError = response.message;
      }
    } catch (error) {
      console.error("SettingsModal: Error syncing tools", error);
      toolSyncError =
        error instanceof Error ? error.message : "Unknown error occurred";
    } finally {
      isToolSyncing = false;
    }
  }

  $: if ($currentMission === null) {
    console.log("SettingsModal: Mission cleared, resetting tool selections");
  }
</script>

<div class="space-y-6">
  <div>
    <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
      Tools
    </h4>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Configure which tools are available for your current mission.
    </p>
  </div>

  <!-- Tool sync status indicators -->
  {#if isToolSyncing}
    <div
      class="flex items-center gap-2 mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded"
    >
      <Spinner size="4" />
      <span class="text-sm text-blue-600 dark:text-blue-400"
        >Syncing tool changes...</span
      >
    </div>
  {/if}

  <!-- Tool sync error -->
  {#if toolSyncError}
    <Alert color="red" class="mb-4">
      <span class="font-medium">Sync Error:</span>
      {toolSyncError}
    </Alert>
  {/if}

  <!-- Mission context info -->
  {#if $currentMission}
    <div class="mb-4 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
      <p class="font-medium text-gray-700 dark:text-gray-300">
        Mission: {$currentMission.title}
      </p>
      <p class="text-gray-500">
        {$currentMission.tools?.length || 0} tools connected
      </p>
    </div>
  {:else}
    <div class="mb-4 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
      <p class="text-yellow-600 dark:text-yellow-400">
        No mission selected. Tool changes will not be saved.
      </p>
    </div>
  {/if}

  <ToolSelector
    {selectedTools}
    on:selectionChange={handleToolSelectionChange}
  />
</div>
