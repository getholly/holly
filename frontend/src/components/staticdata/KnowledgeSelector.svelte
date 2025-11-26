<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { getKnowledge } from "$lib/apis/staticdata/api.knowledge";
  import { Checkbox, P, Tooltip } from "flowbite-svelte";
  import type { KnowledgeSchema } from "holly-api";
  import { InfoCircleOutline } from "flowbite-svelte-icons";
  import { currentMission } from "$lib/store/mission/mission.store";

  export let selectedKnowledge: number[] = [];
  let knowledgeItems: KnowledgeSchema[] = [];
  let isLoading = true;
  let error: string | null = null;

  const dispatch = createEventDispatcher();

  onMount(async () => {
    try {
      knowledgeItems = await getKnowledge();
      isLoading = false;
    } catch (e) {
      error = "Failed to load knowledge items";
      isLoading = false;
      console.error("Error loading knowledge items:", e);
    }
  });

  // Reactive statement to update selected knowledge when mission changes
  $: if (
    $currentMission &&
    $currentMission.knowledge_items &&
    knowledgeItems.length > 0
  ) {
    console.log(
      "KnowledgeSelector: Mission changed, updating selected knowledge",
      $currentMission.knowledge_items,
    );
    updateSelectedKnowledgeFromMission($currentMission.knowledge_items);
  }

  /**
   * Update selected knowledge items based on current mission
   */
  function updateSelectedKnowledgeFromMission(
    missionKnowledge: Array<{ id: number; name: string }>,
  ) {
    const missionKnowledgeIds = missionKnowledge.map((item) => item.id);
    console.log(
      "KnowledgeSelector: Setting selected knowledge from mission",
      missionKnowledgeIds,
    );
    selectedKnowledge = missionKnowledgeIds;
  }

  function handleKnowledgeSelection(item: KnowledgeSchema, event: Event) {
    const isChecked = (event.target as HTMLInputElement).checked;
    console.log(
      "KnowledgeSelector: Knowledge selection changed",
      item.name,
      isChecked,
    );
    if (isChecked) {
      selectedKnowledge = [...selectedKnowledge, item.id];
    } else {
      selectedKnowledge = selectedKnowledge.filter((id) => id !== item.id);
    }
    dispatch("selectionChange", { selectedKnowledge });
  }
</script>

<div class="knowledge-selector">
  <h3 class="text-lg font-semibold mb-2">Knowledge Items</h3>

  <!-- Mission context info -->
  {#if $currentMission}
    <div class="mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-sm">
      <p class="font-medium text-blue-700 dark:text-blue-300">
        Mission: {$currentMission.title}
      </p>
      <p class="text-blue-600 dark:text-blue-400">
        {$currentMission.knowledge_items?.length || 0} knowledge items configured
      </p>
    </div>
  {:else}
    <div class="mb-4 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
      <p class="text-yellow-600 dark:text-yellow-400">
        No mission selected. Knowledge selections will not be saved to a
        mission.
      </p>
    </div>
  {/if}

  {#if isLoading}
    <P>Loading knowledge items...</P>
  {:else if error}
    <P color="red">{error}</P>
  {:else if knowledgeItems.length === 0}
    <P>No knowledge items available</P>
  {:else}
    <div class="grid grid-cols-1 gap-2">
      {#each knowledgeItems as item (item.id)}
        <div class="flex items-center">
          <Checkbox
            id={`knowledge-${item.id}`}
            checked={selectedKnowledge.includes(item.id)}
            on:change={(e) => handleKnowledgeSelection(item, e)}
          />
          <label for={`knowledge-${item.id}`} class="ml-2 flex items-center">
            {item.name}
            {#if $currentMission && $currentMission.knowledge_items?.some((k) => k.id === item.id)}
              <span
                class="ml-2 px-1 py-0.5 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 text-xs rounded"
              >
                Mission
              </span>
            {/if}
            {#if item.description}
              <span class="ml-1">
                <Tooltip content={item.description}>
                  <InfoCircleOutline size="1x" class="text-gray-500" />
                </Tooltip>
              </span>
            {/if}
          </label>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .knowledge-selector {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
  }
</style>
