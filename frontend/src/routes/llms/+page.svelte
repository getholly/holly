<script lang="ts">
  import { onMount } from "svelte";
  import {
    getLLMs,
    createLLM,
    updateLLM,
    deleteLLM,
    type LLMCreateData,
    type LLMUpdateData,
  } from "$lib/apis/staticdata/api.llm";
  import {
    listApiKeys,
    createApiKey,
    updateApiKey,
    deleteApiKey,
    type UserLLMApiKeySchema,
  } from "$lib/apis/llmkeys/api.llmkeys";
  import type { LLMSchema } from "holly-api";
  import {
    Button,
    Modal,
    Label,
    Input,
    Textarea,
    Badge,
    Table,
    TableBody,
    TableBodyCell,
    TableBodyRow,
    TableHead,
    TableHeadCell,
    Spinner,
  } from "flowbite-svelte";
  import {
    PlusOutline,
    EditOutline,
    TrashBinOutline,
    CheckOutline,
    CloseOutline,
    EyeOutline,
    EyeSlashOutline,
    SearchOutline,
  } from "flowbite-svelte-icons";

  // Extended LLM type with API key information
  interface LLMWithApiKey extends LLMSchema {
    hasApiKey: boolean;
    apiKeyId?: number;
    maskedApiKey?: string;
    isEditingLLM?: boolean;
    isEditingApiKey?: boolean;
    editData?: Partial<LLMSchema>;
    showApiKey?: boolean;
  }

  let llms: LLMWithApiKey[] = [];
  let apiKeys: UserLLMApiKeySchema[] = [];
  let loading = true;
  let error = "";

  // Modal states
  let showAddLLMModal = false;
  let showDeleteConfirmModal = false;
  let llmToDelete: LLMWithApiKey | null = null;

  // Form data
  let newLLM: LLMCreateData = {
    name: "",
    full_name: "",
    base_url: "",
    system_prompt: "",
    temperature: 0.7,
    max_tokens: 4096,
    top_p: null,
    top_k: null,
    min_p: null,
  };

  let newApiKeyValue = "";
  let editingApiKeyLLMId: number | null = null;
  let searchQuery = "";

  // Filter LLMs based on search query
  $: filteredLLMs = llms.filter((llm) => {
    if (!searchQuery.trim()) return true;
    const query = searchQuery.toLowerCase();
    return (
      llm.name?.toLowerCase().includes(query) ||
      llm.full_name?.toLowerCase().includes(query) ||
      llm.base_url?.toLowerCase().includes(query) ||
      llm.system_prompt?.toLowerCase().includes(query)
    );
  });

  async function loadData() {
    try {
      loading = true;
      error = "";

      const [llmsData, apiKeysData] = await Promise.all([
        getLLMs(),
        listApiKeys(),
      ]);

      apiKeys = apiKeysData;

      // Merge LLM data with API key information
      llms = llmsData.map((llm) => {
        const apiKey = apiKeys.find((key) => key.llm_id === llm.id);
        return {
          ...llm,
          hasApiKey: !!apiKey,
          apiKeyId: apiKey?.id,
          maskedApiKey: apiKey?.api_key,
          isEditingLLM: false,
          isEditingApiKey: false,
          showApiKey: false,
        };
      });
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to load data";
      console.error("Error loading LLMs and API keys:", err);
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadData();
  });

  function startEditLLM(llm: LLMWithApiKey) {
    if (llm.is_system) return; // Can't edit system LLMs

    llms = llms.map((l) =>
      l.id === llm.id ? { ...l, isEditingLLM: true, editData: { ...l } } : l,
    );
  }

  function cancelEditLLM(llmId: number) {
    llms = llms.map((l) =>
      l.id === llmId ? { ...l, isEditingLLM: false, editData: undefined } : l,
    );
  }

  async function saveEditLLM(llm: LLMWithApiKey) {
    if (!llm.editData) return;

    try {
      const updateData: LLMUpdateData = {
        name: llm.editData.name,
        full_name: llm.editData.full_name,
        base_url: llm.editData.base_url,
        system_prompt: llm.editData.system_prompt,
        temperature: llm.editData.temperature,
        max_tokens: llm.editData.max_tokens,
        top_p: llm.editData.top_p,
        top_k: llm.editData.top_k,
        min_p: llm.editData.min_p,
      };

      const updated = await updateLLM(llm.id, updateData);

      llms = llms.map((l) =>
        l.id === llm.id
          ? { ...l, ...updated, isEditingLLM: false, editData: undefined }
          : l,
      );
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to update LLM";
      console.error("Error updating LLM:", err);
    }
  }

  function confirmDelete(llm: LLMWithApiKey) {
    llmToDelete = llm;
    showDeleteConfirmModal = true;
  }

  async function executeDelete() {
    if (!llmToDelete) return;

    try {
      await deleteLLM(llmToDelete.id);
      llms = llms.filter((l) => l.id !== llmToDelete.id);
      showDeleteConfirmModal = false;
      llmToDelete = null;
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to delete LLM";
      console.error("Error deleting LLM:", err);
    }
  }

  async function handleAddLLM() {
    try {
      const created = await createLLM(newLLM);
      llms = [
        ...llms,
        {
          ...created,
          hasApiKey: false,
          isEditingLLM: false,
          isEditingApiKey: false,
        },
      ];
      showAddLLMModal = false;

      // Reset form
      newLLM = {
        name: "",
        full_name: "",
        base_url: "",
        system_prompt: "",
        temperature: 0.7,
        max_tokens: 4096,
        top_p: null,
        top_k: null,
        min_p: null,
      };
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to create LLM";
      console.error("Error creating LLM:", err);
    }
  }

  function startEditApiKey(llm: LLMWithApiKey) {
    llms = llms.map((l) =>
      l.id === llm.id ? { ...l, isEditingApiKey: true } : l,
    );
    editingApiKeyLLMId = llm.id;
    newApiKeyValue = "";
  }

  function cancelEditApiKey(llmId: number) {
    llms = llms.map((l) =>
      l.id === llmId ? { ...l, isEditingApiKey: false } : l,
    );
    editingApiKeyLLMId = null;
    newApiKeyValue = "";
  }

  async function saveApiKey(llm: LLMWithApiKey) {
    if (!newApiKeyValue.trim()) {
      error = "API key cannot be empty";
      return;
    }

    try {
      if (llm.hasApiKey && llm.apiKeyId) {
        // Update existing key
        const updated = await updateApiKey(llm.apiKeyId, {
          api_key: newApiKeyValue,
        });
        llms = llms.map((l) =>
          l.id === llm.id
            ? { ...l, maskedApiKey: updated.api_key, isEditingApiKey: false }
            : l,
        );
      } else {
        // Create new key
        const created = await createApiKey({
          llm_id: llm.id,
          api_key: newApiKeyValue,
        });
        llms = llms.map((l) =>
          l.id === llm.id
            ? {
                ...l,
                hasApiKey: true,
                apiKeyId: created.id,
                maskedApiKey: created.api_key,
                isEditingApiKey: false,
              }
            : l,
        );
      }

      editingApiKeyLLMId = null;
      newApiKeyValue = "";
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to save API key";
      console.error("Error saving API key:", err);
    }
  }

  async function removeApiKey(llm: LLMWithApiKey) {
    if (!llm.apiKeyId) return;

    if (!confirm("Are you sure you want to remove this API key?")) return;

    try {
      await deleteApiKey(llm.apiKeyId);
      llms = llms.map((l) =>
        l.id === llm.id
          ? {
              ...l,
              hasApiKey: false,
              apiKeyId: undefined,
              maskedApiKey: undefined,
            }
          : l,
      );
    } catch (err) {
      error = err instanceof Error ? err.message : "Failed to remove API key";
      console.error("Error removing API key:", err);
    }
  }
</script>

<div class="container mx-auto p-6 max-h-screen overflow-y-auto">
  <div
    class="mb-6 flex justify-between items-center sticky top-0 bg-white dark:bg-gray-900 z-10 pb-4"
  >
    <div>
      <h1 class="text-3xl font-bold text-gray-900 dark:text-white">
        LLM Management
      </h1>
      <p class="text-gray-600 dark:text-gray-400 mt-2">
        Manage AI models and API keys
      </p>
    </div>
    <div class="flex items-center gap-4">
      <div class="relative">
        <div class="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <SearchOutline class="w-4 h-4 text-gray-500 dark:text-gray-400" />
        </div>
        <input
          type="text"
          bind:value={searchQuery}
          placeholder="Search LLMs..."
          class="block w-64 pl-10 pr-3 py-2 text-sm border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500"
        />
      </div>
      <Button on:click={() => (showAddLLMModal = true)}>
        <PlusOutline class="w-4 h-4 mr-2" />
        Add Custom LLM
      </Button>
    </div>
  </div>

  {#if error}
    <div
      class="mb-4 p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-200 rounded-lg"
    >
      {error}
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center items-center py-12">
      <Spinner size="12" />
    </div>
  {:else if llms.length === 0}
    <div class="text-center py-12">
      <p class="text-gray-500 dark:text-gray-400">
        No LLMs configured. Add your first custom LLM to get started.
      </p>
    </div>
  {:else if filteredLLMs.length === 0}
    <div class="text-center py-12">
      <p class="text-gray-500 dark:text-gray-400">
        No LLMs match your search criteria.
      </p>
    </div>
  {:else}
    <div class="overflow-x-auto shadow-md rounded-lg">
      <Table>
        <TableHead>
          <TableHeadCell>Name</TableHeadCell>
          <TableHeadCell>Model ID</TableHeadCell>
          <TableHeadCell>Base URL</TableHeadCell>
          <TableHeadCell>Type</TableHeadCell>
          <TableHeadCell>API Key</TableHeadCell>
          <TableHeadCell>Actions</TableHeadCell>
        </TableHead>
        <TableBody>
          {#each filteredLLMs as llm (llm.id)}
            <TableBodyRow>
              <!-- Name -->
              <TableBodyCell>
                {#if llm.isEditingLLM && llm.editData}
                  <Input
                    bind:value={llm.editData.name}
                    size="sm"
                    class="w-full"
                  />
                {:else}
                  <div class="font-medium">{llm.name}</div>
                {/if}
              </TableBodyCell>

              <!-- Model ID -->
              <TableBodyCell>
                {#if llm.isEditingLLM && llm.editData}
                  <Input
                    bind:value={llm.editData.full_name}
                    size="sm"
                    class="w-full"
                  />
                {:else}
                  <code
                    class="text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded"
                    >{llm.full_name}</code
                  >
                {/if}
              </TableBodyCell>

              <!-- Base URL -->
              <TableBodyCell>
                {#if llm.isEditingLLM && llm.editData}
                  <Input
                    bind:value={llm.editData.base_url}
                    size="sm"
                    class="w-full"
                    placeholder="Optional"
                  />
                {:else}
                  <span class="text-sm text-gray-600 dark:text-gray-400"
                    >{llm.base_url || "Default"}</span
                  >
                {/if}
              </TableBodyCell>

              <!-- Type Badge -->
              <TableBodyCell>
                {#if llm.is_system}
                  <Badge color="blue">System</Badge>
                {:else}
                  <Badge color="green">Custom</Badge>
                {/if}
              </TableBodyCell>

              <!-- API Key -->
              <TableBodyCell>
                {#if llm.isEditingApiKey}
                  <div class="flex gap-2 items-center">
                    <Input
                      type="password"
                      bind:value={newApiKeyValue}
                      placeholder="Enter API key"
                      size="sm"
                      class="w-48"
                    />
                    <Button
                      size="xs"
                      color="green"
                      on:click={() => saveApiKey(llm)}
                    >
                      <CheckOutline class="w-3 h-3" />
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      on:click={() => cancelEditApiKey(llm.id)}
                    >
                      <CloseOutline class="w-3 h-3" />
                    </Button>
                  </div>
                {:else if llm.hasApiKey}
                  <div class="flex gap-2 items-center">
                    <code
                      class="text-sm bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded"
                      >{llm.maskedApiKey}</code
                    >
                    <Button
                      size="xs"
                      color="blue"
                      on:click={() => startEditApiKey(llm)}
                    >
                      <EditOutline class="w-3 h-3" />
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      on:click={() => removeApiKey(llm)}
                    >
                      <TrashBinOutline class="w-3 h-3" />
                    </Button>
                  </div>
                {:else}
                  <Button size="xs" on:click={() => startEditApiKey(llm)}>
                    <PlusOutline class="w-3 h-3 mr-1" />
                    Add Key
                  </Button>
                {/if}
              </TableBodyCell>

              <!-- Actions -->
              <TableBodyCell>
                {#if llm.isEditingLLM}
                  <div class="flex gap-2">
                    <Button
                      size="xs"
                      color="green"
                      on:click={() => saveEditLLM(llm)}
                    >
                      <CheckOutline class="w-3 h-3" />
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      on:click={() => cancelEditLLM(llm.id)}
                    >
                      <CloseOutline class="w-3 h-3" />
                    </Button>
                  </div>
                {:else if !llm.is_system}
                  <div class="flex gap-2">
                    <Button
                      size="xs"
                      color="blue"
                      on:click={() => startEditLLM(llm)}
                    >
                      <EditOutline class="w-3 h-3" />
                    </Button>
                    <Button
                      size="xs"
                      color="red"
                      on:click={() => confirmDelete(llm)}
                    >
                      <TrashBinOutline class="w-3 h-3" />
                    </Button>
                  </div>
                {:else}
                  <span class="text-gray-400 text-sm">Read-only</span>
                {/if}
              </TableBodyCell>
            </TableBodyRow>
          {/each}
        </TableBody>
      </Table>
    </div>
  {/if}
</div>

<!-- Add LLM Modal -->
<Modal bind:open={showAddLLMModal} size="lg" title="Add Custom LLM">
  <form on:submit|preventDefault={handleAddLLM} class="space-y-4">
    <div>
      <Label for="name">Name *</Label>
      <Input
        id="name"
        bind:value={newLLM.name}
        placeholder="My Custom LLM"
        required
      />
    </div>

    <div>
      <Label for="full_name">Model ID *</Label>
      <Input
        id="full_name"
        bind:value={newLLM.full_name}
        placeholder="openai/gpt-4"
        required
      />
      <p class="text-sm text-gray-500 mt-1">
        Format: provider/model (e.g., openai/gpt-4, anthropic/claude-3-opus)
      </p>
    </div>

    <div>
      <Label for="base_url">Base URL</Label>
      <Input
        id="base_url"
        bind:value={newLLM.base_url}
        placeholder="https://api.openai.com/v1"
      />
      <p class="text-sm text-gray-500 mt-1">
        Leave empty for default provider URL
      </p>
    </div>

    <div>
      <Label for="system_prompt">System Prompt</Label>
      <Textarea
        id="system_prompt"
        bind:value={newLLM.system_prompt}
        rows="3"
        placeholder="You are a helpful assistant..."
      />
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div>
        <Label for="temperature">Temperature</Label>
        <Input
          id="temperature"
          type="number"
          step="0.1"
          min="0"
          max="2"
          bind:value={newLLM.temperature}
        />
      </div>

      <div>
        <Label for="max_tokens">Max Tokens</Label>
        <Input id="max_tokens" type="number" bind:value={newLLM.max_tokens} />
      </div>
    </div>

    <div class="flex justify-end gap-2 pt-4">
      <Button color="alternative" on:click={() => (showAddLLMModal = false)}
        >Cancel</Button
      >
      <Button type="submit" color="blue">Create LLM</Button>
    </div>
  </form>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteConfirmModal} size="sm" title="Confirm Delete">
  <div class="text-center">
    <p class="mb-4">
      Are you sure you want to delete <strong>{llmToDelete?.name}</strong>?
    </p>
    <p class="text-sm text-gray-500 mb-6">This action cannot be undone.</p>

    <div class="flex justify-center gap-4">
      <Button
        color="alternative"
        on:click={() => (showDeleteConfirmModal = false)}>Cancel</Button
      >
      <Button color="red" on:click={executeDelete}>Delete</Button>
    </div>
  </div>
</Modal>

<style>
  :global(table) {
    min-width: 100%;
  }
</style>
