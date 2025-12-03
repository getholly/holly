<script lang="ts">
  import { Button, Card, Badge } from "flowbite-svelte";
  import {
    CogOutline,
    TrashBinOutline,
    CheckCircleSolid,
    ArrowRightOutline,
  } from "flowbite-svelte-icons";
  import type { MissionSummary } from "holly-api";
  import { createEventDispatcher } from "svelte";

  export let mission: MissionSummary;
  export let isSelected = false;

  const dispatch = createEventDispatcher();

  function handleSelect() {
    dispatch("select", mission);
  }

  function handleEdit(e: Event) {
    e.stopPropagation();
    dispatch("edit", mission);
  }

  function handleDelete(e: Event) {
    e.stopPropagation();
    dispatch("delete", mission);
  }
</script>

<div
  class="relative group transition-all duration-300 hover:shadow-xl hover:-translate-y-1 cursor-pointer h-full rounded-xl overflow-hidden"
  on:click={handleSelect}
  on:keydown={(e) => e.key === "Enter" && handleSelect()}
  role="button"
  tabindex="0"
>
  <Card
    class={`h-full flex flex-col justify-between border ${isSelected ? "border-blue-500 dark:border-blue-500 shadow-md" : "border-gray-200 dark:border-gray-700 hover:border-cyan-400 dark:hover:border-cyan-600"} transition-colors duration-300 bg-white dark:bg-slate-800/50 backdrop-blur-sm`}
    padding="lg"
  >
    <!-- Header -->
    <div class="flex justify-between items-start mb-2">
      <h3 class="text-xl font-bold tracking-tight text-gray-900 dark:text-white truncate pr-2">
        {mission.title}
      </h3>
      {#if isSelected}
        <CheckCircleSolid class="text-blue-500 w-6 h-6 flex-shrink-0" />
      {/if}
    </div>

    <!-- Details -->
    <div class="flex-grow space-y-3">
      <div class="flex flex-wrap gap-2 text-sm mt-3">
        <Badge color={mission.state === 'active' ? 'green' : 'yellow'}>
          {mission.state}
        </Badge>
        
        <Badge color="indigo">
          Branch: {mission.branch_name || "Default"}
        </Badge>

        <Badge color="purple">
          Repos: {mission.repository_count || 0}
        </Badge>
        
        <!-- LLM info if available -->
        {#if mission.llm}
            <Badge color="dark">
                {mission.llm.name}
            </Badge>
        {/if}
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-between items-center mt-6 pt-4 border-t border-gray-100 dark:border-gray-700">
      <Button
        size="xs"
        outline
        color="blue"
        on:click={handleSelect}
        class="opacity-0 group-hover:opacity-100 transition-opacity"
      >
        Select <ArrowRightOutline class="w-3 h-3 ml-1" />
      </Button>

      <div class="flex gap-2">
        <Button size="xs" color="light" class="p-2" on:click={handleEdit}>
          <CogOutline class="w-4 h-4" />
        </Button>
        <Button size="xs" color="red" class="p-2" on:click={handleDelete}>
          <TrashBinOutline class="w-4 h-4" />
        </Button>
      </div>
    </div>
  </Card>
</div>
