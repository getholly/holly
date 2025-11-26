<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";
  import { setSelections } from "$lib/store/chat/repo.store";
  import type { RepoSelection } from "$lib/types/githubTypes";

  export let open = false;

  const dispatch = createEventDispatcher();

  let currentSelections: RepoSelection[] = [];

  function handleSelectionChange(event: CustomEvent<RepoSelection[]>) {
    currentSelections = event.detail || [];
  }

  function apply() {
    setSelections(currentSelections);
    dispatch("close");
  }

  function close() {
    dispatch("close");
  }
</script>

{#if open}
  <div class="fixed inset-0 z-50 flex items-center justify-center">
    <div
      class="absolute inset-0 bg-black bg-opacity-40"
      on:click={close}
      on:keydown={(e) => e.key === "Escape" && close()}
      role="button"
      tabindex="-1"
      aria-label="Close modal"
    ></div>
    <div
      class="relative bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-2xl p-4"
    >
      <div class="flex items-center justify-between mb-4">
        <h3 class="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Select Repository and Branch
        </h3>
        <button
          class="text-gray-500 hover:text-gray-700 dark:text-gray-400"
          on:click={close}>✕</button
        >
      </div>
      <div class="max-h-[70vh] overflow-y-auto pr-1">
        <GitMultiSelect on:selectionchange={handleSelectionChange} />
      </div>
      <div class="mt-4 flex justify-end gap-2">
        <button
          class="px-3 py-1.5 rounded-md bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          on:click={close}>Cancel</button
        >
        <button
          class="px-3 py-1.5 rounded-md bg-blue-600 text-white"
          on:click={apply}>Apply</button
        >
      </div>
    </div>
  </div>
{/if}
