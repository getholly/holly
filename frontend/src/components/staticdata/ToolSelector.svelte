<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { getTools } from "$lib/apis/staticdata/api.tools";
  import { Checkbox, P } from "flowbite-svelte";
  import type { ToolSchema } from "holly-api";
  import { currentMission } from "$lib/store/mission/mission.store";

  export let selectedTools: number[] = [];
  let tools: ToolSchema[] = [];
  let isLoading = true;
  let error: string | null = null;

  const dispatch = createEventDispatcher();

  onMount(async () => {
    try {
      tools = await getTools();
      isLoading = false;
    } catch (e) {
      error = "Failed to load tools";
      isLoading = false;
      console.error("Error loading tools:", e);
    }
  });

  // Reactive statement to update selected tools when mission changes
  $: if ($currentMission && $currentMission.tools && tools.length > 0) {
    console.log(
      "ToolSelector: Mission changed, updating selected tools",
      $currentMission.tools,
    );
    updateSelectedToolsFromMission($currentMission.tools);
  }

  /**
   * Update selected tools based on current mission
   */
  function updateSelectedToolsFromMission(
    missionTools: Array<{ id: number; name: string }>,
  ) {
    const missionToolIds = missionTools.map((tool) => tool.id);
    console.log(
      "ToolSelector: Setting selected tools from mission",
      missionToolIds,
    );
    selectedTools = missionToolIds;
  }

  function handleToolSelection(tool: ToolSchema, event: Event) {
    const isChecked = (event.target as HTMLInputElement).checked;
    console.log("ToolSelector: Tool selection changed", tool.name, isChecked);
    if (isChecked) {
      selectedTools = [...selectedTools, tool.id];
    } else {
      selectedTools = selectedTools.filter((id) => id !== tool.id);
    }
    dispatch("selectionChange", { selectedTools });
  }
</script>

<div class="tool-selector">
  <h3 class="text-lg font-semibold mb-2">Available Tools</h3>

  <!-- Mission context info -->
  {#if $currentMission}
    <div class="mb-4 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-sm">
      <p class="font-medium text-blue-700 dark:text-blue-300">
        Mission: {$currentMission.title}
      </p>
      <p class="text-blue-600 dark:text-blue-400">
        {$currentMission.tools?.length || 0} tools configured
      </p>
    </div>
  {:else}
    <div class="mb-4 p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded text-sm">
      <p class="text-yellow-600 dark:text-yellow-400">
        No mission selected. Tool selections will not be saved to a mission.
      </p>
    </div>
  {/if}

  {#if isLoading}
    <P>Loading available tools...</P>
  {:else if error}
    <P color="red">{error}</P>
  {:else if tools.length === 0}
    <P>No tools available</P>
  {:else}
    <div class="grid grid-cols-1 gap-2">
      {#each tools as tool (tool.id)}
        <div class="flex items-center">
          <Checkbox
            id={`tool-${tool.id}`}
            checked={selectedTools.includes(tool.id)}
            on:change={(e) => handleToolSelection(tool, e)}
          />
          <label for={`tool-${tool.id}`} class="ml-2 flex items-center">
            {tool.name}
            {#if $currentMission && $currentMission.tools?.some((t) => t.id === tool.id)}
              <span
                class="ml-2 px-1 py-0.5 bg-blue-100 dark:bg-blue-800 text-blue-800 dark:text-blue-200 text-xs rounded"
              >
                Mission
              </span>
            {/if}
          </label>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .tool-selector {
    padding: 1rem;
    border-radius: 0.5rem;
    background-color: #f9fafb;
    border: 1px solid #e5e7eb;
  }
</style>
