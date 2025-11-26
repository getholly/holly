<script lang="ts">
  import { Alert, Spinner } from "flowbite-svelte";
  import KnowledgeSelector from "$components/staticdata/KnowledgeSelector.svelte";
  import { currentMission } from "$lib/store/mission/mission.store";
  import { getMission, setKnowledgeItems } from "$lib/apis/mission/api.mission";

  // Knowledge Base section state
  let selectedKnowledge: number[] = [];
  let knowledgeSyncError: string | null = null;
  let isKnowledgeSyncing = false;

  // Update knowledge selections when mission changes
  $: if ($currentMission?.knowledge_items) {
    console.log(
      "SettingsModalKnowledge: Current mission changed, updating knowledge selections",
      $currentMission.title,
      $currentMission.knowledge_items,
    );
    updateKnowledgeSelections($currentMission.knowledge_items);
  } else if ($currentMission === null) {
    console.log(
      "SettingsModalKnowledge: Mission cleared, resetting knowledge selections",
    );
    selectedKnowledge = [];
  }

  function updateKnowledgeSelections(missionKnowledge: any[]) {
    console.log(
      "SettingsModalKnowledge: updateKnowledgeSelections called with",
      missionKnowledge,
    );

    if (!missionKnowledge || missionKnowledge.length === 0) {
      console.log(
        "SettingsModalKnowledge: No mission knowledge, clearing selections",
      );
      selectedKnowledge = [];
      return;
    }

    const knowledgeIds = missionKnowledge.map((item) => item.id);
    console.log(
      "SettingsModalKnowledge: Setting selected knowledge from mission",
      knowledgeIds,
    );
    selectedKnowledge = knowledgeIds;
  }

  async function handleKnowledgeSelectionChange(event: CustomEvent) {
    const newSelectedKnowledge = event.detail.selectedKnowledge;

    if (!$currentMission) {
      console.warn(
        "No current mission selected, cannot sync knowledge changes",
      );
      return;
    }

    console.log(
      "SettingsModalKnowledge: Syncing knowledge changes to mission",
      $currentMission.id,
      newSelectedKnowledge,
    );

    isKnowledgeSyncing = true;
    knowledgeSyncError = null;

    try {
      const response = await setKnowledgeItems($currentMission.id, {
        knowledge_item_ids: newSelectedKnowledge,
      });

      if (response.success) {
        console.log(
          "SettingsModalKnowledge: Knowledge sync successful",
          response.message,
        );
        const updatedMission = await getMission($currentMission.id);
        currentMission.set(updatedMission);
      } else {
        console.error(
          "SettingsModalKnowledge: Knowledge sync failed",
          response.message,
        );
        knowledgeSyncError = response.message;
      }
    } catch (error) {
      console.error(
        "SettingsModalKnowledge: Error syncing knowledge items",
        error,
      );
      knowledgeSyncError =
        error instanceof Error ? error.message : "Unknown error occurred";
    } finally {
      isKnowledgeSyncing = false;
    }
  }
</script>

<div class="space-y-6">
  <div>
    <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
      Knowledge Base
    </h4>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Configure which knowledge items are available for your current mission.
    </p>
  </div>

  <!-- Knowledge sync status indicators -->
  {#if isKnowledgeSyncing}
    <div
      class="flex items-center gap-2 mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded"
    >
      <Spinner size="4" />
      <span class="text-sm text-blue-600 dark:text-blue-400"
        >Syncing knowledge changes...</span
      >
    </div>
  {/if}

  <!-- Knowledge sync error -->
  {#if knowledgeSyncError}
    <Alert color="red" class="mb-4">
      <span class="font-medium">Sync Error:</span>
      {knowledgeSyncError}
    </Alert>
  {/if}

  <!-- Mission context info -->
  {#if $currentMission}
    <div class="mb-4 p-2 bg-gray-50 dark:bg-gray-800 rounded text-sm">
      <p class="font-medium text-gray-700 dark:text-gray-300">
        Mission: {$currentMission.title}
      </p>
      <p class="text-gray-500">
        {$currentMission.knowledge_items?.length || 0} knowledge items connected
      </p>
    </div>
  {:else}
    <div class="mb-4 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
      <p class="text-yellow-600 dark:text-yellow-400">
        No mission selected. Knowledge changes will not be saved.
      </p>
    </div>
  {/if}

  <KnowledgeSelector
    {selectedKnowledge}
    on:selectionChange={handleKnowledgeSelectionChange}
  />
</div>
