<script lang="ts">
  import { onMount, createEventDispatcher } from "svelte";
  import { Select, Spinner } from "flowbite-svelte";
  import {
    loadLLMs,
    llmModels,
    formatLLMsForDropdown,
  } from "$lib/store/llm/llm.store";

  export let selectedLlmId = "";

  const dispatch = createEventDispatcher();
  let loading = false;
  let error = "";
  let options = [];

  // Reactive statement for options
  $: options = formatLLMsForDropdown($llmModels);

  // Reactive statement to initialize selection if needed
  $: if (!selectedLlmId && options.length > 0) {
    selectedLlmId = options[0].value;
    handleModelChange();
  }

  onMount(async () => {
    await fetchLlms();
  });

  async function fetchLlms() {
    loading = true;
    error = "";

    try {
      await loadLLMs();
    } catch (err) {
      console.error("Error loading LLM models:", err);
      error = "Failed to load LLM models";
    } finally {
      loading = false;
    }
  }

  function handleModelChange() {
    const selectedModel = $llmModels.find(
      (model) => model.id.toString() === selectedLlmId,
    );
    dispatch("llmSelected", {
      id: selectedLlmId,
      name: selectedModel?.name || "",
    });
  }
</script>

<div class="h-8">
  {#if loading}
    <div class="flex items-center justify-center h-full">
      <Spinner size="3" />
    </div>
  {:else if error}
    <div class="text-xs text-red-500 text-center">Error</div>
  {:else if $llmModels.length === 0}
    <div class="text-xs text-gray-500 text-center">No models</div>
  {:else}
    <Select
      class="text-xs py-0 px-1 h-8 focus:border-theme-primary dark:focus:border-theme-primary focus:ring-0 dark:bg-gray-800 border-0 bg-transparent"
      size="sm"
      bind:value={selectedLlmId}
      on:change={handleModelChange}
      items={options}
    />
  {/if}
</div>
