<script lang="ts">
  import { Alert, Button, Search } from "flowbite-svelte";
  import {
    EyeOutline,
    EyeSlashOutline,
    SearchOutline,
    CloseOutline,
  } from "flowbite-svelte-icons";
  import { onMount } from "svelte";
  import LlmSelector from "$components/settings/LlmSelector.svelte";
  import { selectedChatLlmId } from "$lib/store/chat/llm.store";
  import {
    llmModels,
    loadLLMs,
    userApiKeysStore,
    loadUserApiKeys,
    addUserApiKey,
    updateUserApiKey,
    removeUserApiKey,
  } from "$lib/store/llm/llm.store";
  import type { SupportedLLMSchema } from "$lib/types/user_llm_api_key";

  // LLM API Key Management State
  let apiKeyInputs: { [llmId: number]: string } = {};
  let apiKeySavingStates: { [llmId: number]: boolean } = {};
  let apiKeyErrorMessages: { [llmId: number]: string | null } = {};
  let apiKeySuccessMessages: { [llmId: number]: string | null } = {};
  let showApiKey: { [llmId: number]: boolean } = {}; // To toggle visibility

  // Search filter state
  let searchTerm = "";

  // Reactive filtering of LLM models
  $: filteredLlmModels = $llmModels.filter((llm) =>
    llm.name.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  // Handle LLM selection
  function handleLlmSelected(event) {
    const { id, name } = event.detail;
    $selectedChatLlmId = id;
    console.log(`LLM selected in settings: ${name} (ID: ${id})`);
  }

  // LLM API Key Management Functions
  onMount(async () => {
    if ($llmModels.length === 0) {
      await loadLLMs();
    }
    await loadUserApiKeys();
    initializeApiKeyInputs();
  });

  $: $userApiKeysStore, initializeApiKeyInputs();

  function initializeApiKeyInputs() {
    const inputs: { [llmId: number]: string } = {};
    if ($llmModels && $userApiKeysStore) {
      $llmModels.forEach((llm) => {
        const existingKey = $userApiKeysStore.find((k) => k.llm_id === llm.id);
        inputs[llm.id] = existingKey ? existingKey.api_key : ""; // Store the masked key
      });
    }
    apiKeyInputs = inputs;
  }

  function clearSearch() {
    searchTerm = "";
  }

  async function handleSaveApiKey(llm: SupportedLLMSchema) {
    const llmId = llm.id;
    const apiKeyToSave = apiKeyInputs[llmId];

    if (
      !apiKeyToSave ||
      apiKeyToSave.trim() === "" ||
      apiKeyToSave.startsWith("**********")
    ) {
      apiKeyErrorMessages[llmId] = "API key cannot be empty or unchanged.";
      setTimeout(() => (apiKeyErrorMessages[llmId] = null), 3000);
      return;
    }

    apiKeySavingStates = { ...apiKeySavingStates, [llmId]: true };
    apiKeyErrorMessages = { ...apiKeyErrorMessages, [llmId]: null };
    apiKeySuccessMessages = { ...apiKeySuccessMessages, [llmId]: null };

    try {
      const existingApiKey = $userApiKeysStore.find((k) => k.llm_id === llmId);
      if (existingApiKey) {
        await updateUserApiKey(existingApiKey.id, { api_key: apiKeyToSave });
        apiKeySuccessMessages[llmId] = `API key for ${llm.name} updated.`;
      } else {
        await addUserApiKey({ llm_id: llmId, api_key: apiKeyToSave });
        apiKeySuccessMessages[llmId] = `API key for ${llm.name} saved.`;
      }
      await loadUserApiKeys(); // Refresh the list and masked keys
      // Do not clear the input here, loadUserApiKeys will update it with the masked version.
      showApiKey[llmId] = false; // Hide after saving
    } catch (error) {
      console.error(`Error saving API key for ${llm.name}:`, error);
      apiKeyErrorMessages[llmId] = error.message || "Failed to save API key.";
    } finally {
      apiKeySavingStates = { ...apiKeySavingStates, [llmId]: false };
      setTimeout(() => {
        apiKeySuccessMessages[llmId] = null;
        apiKeyErrorMessages[llmId] = null;
      }, 3000);
    }
  }

  async function handleDeleteApiKey(llmId: number, llmName: string) {
    const existingApiKey = $userApiKeysStore.find((k) => k.llm_id === llmId);
    if (!existingApiKey) {
      apiKeyErrorMessages[llmId] = "No API key to delete.";
      setTimeout(() => (apiKeyErrorMessages[llmId] = null), 3000);
      return;
    }

    apiKeySavingStates = { ...apiKeySavingStates, [llmId]: true }; // Use saving state for delete as well
    apiKeyErrorMessages = { ...apiKeyErrorMessages, [llmId]: null };
    apiKeySuccessMessages = { ...apiKeySuccessMessages, [llmId]: null };

    try {
      await removeUserApiKey(existingApiKey.id);
      apiKeySuccessMessages[llmId] = `API key for ${llmName} deleted.`;
      apiKeyInputs[llmId] = ""; // Clear input field
      await loadUserApiKeys(); // Refresh list
    } catch (error) {
      console.error(`Error deleting API key for ${llmName}:`, error);
      apiKeyErrorMessages[llmId] = error.message || "Failed to delete API key.";
    } finally {
      apiKeySavingStates = { ...apiKeySavingStates, [llmId]: false };
      setTimeout(() => {
        apiKeySuccessMessages[llmId] = null;
        apiKeyErrorMessages[llmId] = null;
      }, 3000);
    }
  }

  function toggleApiKeyVisibility(llmId: number) {
    showApiKey[llmId] = !showApiKey[llmId];
    if (
      showApiKey[llmId] &&
      apiKeyInputs[llmId] &&
      apiKeyInputs[llmId].startsWith("**********")
    ) {
      // If revealing and current value is masked, prompt user to enter new key or clear for new entry
      // For simplicity, we'll just clear it to force new entry if they want to see it.
      // A better UX might be to fetch the unmasked key if permissions allow, or allow editing directly.
      // For now, this approach encourages re-entry if they want to view/change.
      // apiKeyInputs[llmId] = ''; // Or fetch and display actual key if desired and secure
    }
  }
</script>

<div class="space-y-6">
  <div>
    <h3 class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
      Default Language Model
    </h3>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Choose the default language model for new conversations. This can be
      changed for individual conversations.
    </p>
    <div class="max-w-md">
      <LlmSelector
        bind:selectedLlmId={$selectedChatLlmId}
        on:llmSelected={handleLlmSelected}
      />
    </div>
  </div>

  <hr class="my-6 border-gray-200 dark:border-gray-700" />

  <div>
    <div class="flex items-center justify-between mb-4">
      <h4 class="text-md font-medium text-gray-900 dark:text-white mb-1">
        API Key Management
      </h4>
      <Search
        bind:value={searchTerm}
        placeholder="Search LLM providers..."
        size="md"
        class="w-full"
      >
        <SearchOutline slot="left" class="w-4 h-4" />
        {#if searchTerm}
          <button
            type="button"
            class="p-1 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            on:click={clearSearch}
            title="Clear search"
          >
            <CloseOutline class="w-4 h-4" />
          </button>
        {/if}
      </Search>
    </div>
    <p class="text-sm text-gray-500 dark:text-gray-400 mb-4">
      Manage API keys for different language models. Keys are stored securely.
    </p>

    {#if $llmModels.length === 0}
      <p class="text-sm text-gray-500 dark:text-gray-400">
        Loading available LLMs...
      </p>
    {:else if filteredLlmModels.length === 0}
      <div class="text-center py-8">
        <p class="text-sm text-gray-500 dark:text-gray-400">
          No LLM providers found matching "{searchTerm}"
        </p>
        <button
          class="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-200 mt-2"
          on:click={clearSearch}
        >
          Clear search to see all providers
        </button>
      </div>
    {:else}
      <div class="space-y-4">
        {#each filteredLlmModels as llm (llm.id)}
          {@const userApiKey = $userApiKeysStore.find(
            (k) => k.llm_id === llm.id,
          )}
          <div
            class="p-4 border border-gray-200 dark:border-gray-700 rounded-lg"
          >
            <p class="font-semibold text-gray-800 dark:text-gray-200">
              {llm.name}
            </p>
            <div class="mt-2 flex items-end space-x-2">
              <div class="flex-grow">
                <label
                  for={`apiKey-${llm.id}`}
                  class="text-xs text-gray-600 dark:text-gray-400"
                >
                  API Key ({userApiKey
                    ? showApiKey[llm.id]
                      ? "Visible"
                      : "Masked"
                    : "Not Set"}
                  )
                </label>
                <div class="relative">
                  {#if showApiKey[llm.id]}
                    <input
                      type="text"
                      id={`apiKey-${llm.id}`}
                      class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                      placeholder={userApiKey
                        ? showApiKey[llm.id]
                          ? "Enter new key to update"
                          : apiKeyInputs[llm.id] || "Enter API Key"
                        : "Enter API Key"}
                      bind:value={apiKeyInputs[llm.id]}
                      on:focus={() => {
                        if (
                          apiKeyInputs[llm.id] &&
                          apiKeyInputs[llm.id].startsWith("**********")
                        )
                          apiKeyInputs[llm.id] = "";
                      }}
                    />
                  {:else}
                    <input
                      type="password"
                      id={`apiKey-${llm.id}`}
                      class="bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
                      placeholder={userApiKey
                        ? showApiKey[llm.id]
                          ? "Enter new key to update"
                          : apiKeyInputs[llm.id] || "Enter API Key"
                        : "Enter API Key"}
                      bind:value={apiKeyInputs[llm.id]}
                      on:focus={() => {
                        if (
                          apiKeyInputs[llm.id] &&
                          apiKeyInputs[llm.id].startsWith("**********")
                        )
                          apiKeyInputs[llm.id] = "";
                      }}
                    />
                  {/if}
                  <button
                    type="button"
                    class="absolute inset-y-0 right-0 px-3 flex items-center text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                    on:click={() => toggleApiKeyVisibility(llm.id)}
                    title={showApiKey[llm.id] ? "Hide API Key" : "Show API Key"}
                  >
                    {#if showApiKey[llm.id]}
                      <EyeOutline class="w-5 h-5" />
                    {:else}
                      <EyeSlashOutline class="w-5 h-5" />
                    {/if}
                  </button>
                </div>
              </div>
              <Button
                on:click={() => handleSaveApiKey(llm)}
                isProcessing={apiKeySavingStates[llm.id]}
                disabled={apiKeySavingStates[llm.id] ||
                  !apiKeyInputs[llm.id] ||
                  apiKeyInputs[llm.id].trim() === "" ||
                  apiKeyInputs[llm.id].startsWith("**********")}
                color={userApiKey ? "alternative" : "blue"}
                class="whitespace-nowrap h-11"
              >
                {userApiKey ? "Update" : "Save"}
              </Button>
              {#if userApiKey}
                <Button
                  on:click={() => handleDeleteApiKey(llm.id, llm.name)}
                  isProcessing={apiKeySavingStates[llm.id] &&
                    !apiKeySuccessMessages[llm.id]}
                  disabled={apiKeySavingStates[llm.id]}
                  color="red"
                  class="whitespace-nowrap h-11"
                >
                  Delete
                </Button>
              {/if}
            </div>
            {#if apiKeyErrorMessages[llm.id]}
              <Alert color="red" class="mt-2 text-xs">
                {apiKeyErrorMessages[llm.id]}
              </Alert>
            {/if}
            {#if apiKeySuccessMessages[llm.id]}
              <Alert color="green" class="mt-2 text-xs">
                {apiKeySuccessMessages[llm.id]}
              </Alert>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>
