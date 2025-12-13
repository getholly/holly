<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import {
    Button,
    Label,
    Select,
    Textarea,
    StepIndicator,
    Spinner,
    Checkbox,
    Input,
  } from "flowbite-svelte";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";

  import {
    wizardActiveStep,
    wizardBranchName,
    wizardSelectedRepos,
    wizardSelectedLlm,
    wizardSelectedTools,
    wizardSelectedKnowledge,
    wizardDescription,
  } from "$lib/store/wizard.store";
  import { base } from "$app/paths";
  import { fade, slide } from "svelte/transition";
  import { llmsApi, toolsApi, knowledgeApi } from "$lib/apis/api.config";
  import type {
    LLMSchema,
    ToolSchema,
    KnowledgeSchema,
    MissionConversationCreate,
    MissionCreate,
    MissionRepoAdd,
  } from "holly-api";
  import {
    createMissionConversation,
    createMission,
    startMissionSse,
  } from "$lib/apis/mission/api.mission";

  $: console.info("Wizard Store Values", {
    $wizardActiveStep,
    $wizardBranchName,
    $wizardSelectedRepos,
    $wizardSelectedLlm,
    $wizardSelectedTools,
    $wizardSelectedKnowledge,
    $wizardDescription,
  });

  // Define steps first so we can use it for totalSteps
  let steps = [
    "Branch Name",
    "Select Repositories",
    "Choose LLM",
    "Tools",
    "Knowledge",
    "Project Description",
  ];
  const totalSteps = steps.length;

  // Add a loading state for navigation
  let isNavigating = false;
  let missionError: string | null = null;

  // LLM loading state
  let llmOptions: Array<{ value: string; name: string }> = [];
  let loadingLlms = false;
  let llmError: string | null = null;

  // Tools loading state
  let toolOptions: Array<{ value: string; name: string; description: string }> =
    [];
  let loadingTools = false;
  let toolsError: string | null = null;

  // Knowledge loading state
  let knowledgeOptions: Array<{
    value: string;
    name: string;
    description: string;
    summary: string;
  }> = [];
  let loadingKnowledge = false;
  let knowledgeError: string | null = null;

  function prevStep() {
    if ($wizardActiveStep > 1) {
      $wizardActiveStep = $wizardActiveStep - 1;
    }
  }

  async function nextStep() {
    if ($wizardActiveStep < totalSteps) {
      $wizardActiveStep = $wizardActiveStep + 1;
      missionError = null; // Clear any previous errors when navigating
    } else {
      // Final step - create mission and navigate to SSE chat
      isNavigating = true;
      missionError = null; // Clear any previous errors
      try {
        // get list of repos to add
        let repoData: MissionRepoAdd[] = [];
        if ($wizardSelectedRepos.length > 0) {
          repoData = $wizardSelectedRepos.map((repo) => ({
            github_id: repo.repo.id,
            branch_name: repo.selectedBranch || "main",
          }));
        }
        // 1. Create the mission
        const missionData: MissionCreate = {
          title: `Mission - ${$wizardBranchName || new Date().toLocaleString()}`,
          description: $wizardDescription,
          branch_name: $wizardBranchName,
          tool_ids: $wizardSelectedTools.map((id) => parseInt(id, 10)),
          repositories: repoData || [],
          knowledge_item_ids: $wizardSelectedKnowledge.map((id) =>
            parseInt(id, 10),
          ),
          llm_id: parseInt($wizardSelectedLlm, 10),
        };

        const mission = await createMission(missionData);

        // 3. Start the mission using SSE for progress updates
        await startMissionSse(mission.id, (evt) => {
          console.log("mission update", evt);
        });

        // 4. Create conversation and redirect to chat
        const conversationTitle = `${missionData.title} - Initial Conversation`;
        const data: MissionConversationCreate = {
          title: conversationTitle,
          initial_message: "",
        };
        const conversation = await createMissionConversation(mission.id, data);
        console.log(`Created conversation: ${conversation}`);
        if (conversation && conversation.conversation_id) {
          await goto(`${base}/sse-chat/${conversation.conversation_id}`);
        } else {
          await goto(`${base}/sse-chat/`);
        }
      } catch (error) {
        console.error("Error creating mission:", error);

        // Determine error message based on error type
        if (error instanceof Event && error.type === "error") {
          // SSE connection error - likely authentication issue
          missionError =
            "Authentication error: Please make sure you are logged in. The session may have expired.";
        } else if (error instanceof Error) {
          missionError = `Failed to create mission: ${error.message}`;
        } else if (
          typeof error === "object" &&
          error !== null &&
          "body" in error
        ) {
          // API error with body
          const apiError = error as any;
          missionError = `Failed to create mission: ${apiError.body?.detail || apiError.body?.message || "Unknown error"}`;
        } else {
          missionError =
            "An unexpected error occurred while creating the mission. Please try again.";
        }

        isNavigating = false;
      }
    }
  }

  function handleRepoSelect(event: CustomEvent) {
    $wizardSelectedRepos = event.detail;
  }

  // Function to fetch available LLMs from the API
  async function fetchLlms() {
    loadingLlms = true;
    llmError = null;

    try {
      const response = await $llmsApi.hollyHollyApiViewsLlmListLlms();
      llmOptions = response.map((llm: LLMSchema) => ({
        value: llm.id.toString(),
        name: llm.name,
      }));

      // If we have LLMs and none selected yet, select the first one
      if (llmOptions.length > 0 && !$wizardSelectedLlm) {
        $wizardSelectedLlm = llmOptions[0].value;
      }
    } catch (error) {
      console.error("Failed to fetch LLMs:", error);
      llmError = "Failed to load LLM options. Please try again.";
    } finally {
      loadingLlms = false;
    }
  }

  // Function to fetch available Tools from the API
  async function fetchTools() {
    loadingTools = true;
    toolsError = null;

    try {
      const response = await $toolsApi.hollyHollyApiViewsToolsListTools();
      toolOptions = response.map((tool: ToolSchema) => ({
        value: tool.id.toString(),
        name: tool.name,
        description: tool.description || "",
      }));
    } catch (error) {
      console.error("Failed to fetch Tools:", error);
      toolsError = "Failed to load Tool options. Please try again.";
    } finally {
      loadingTools = false;
    }
  }

  // Function to fetch available Knowledge from the API
  async function fetchKnowledge() {
    loadingKnowledge = true;
    knowledgeError = null;

    try {
      const response =
        await $knowledgeApi.hollyHollyApiViewsKnowledgeListKnowledge();
      knowledgeOptions = response.map((knowledge: KnowledgeSchema) => ({
        value: knowledge.id.toString(),
        name: knowledge.name,
        description: knowledge.description || "",
        summary: knowledge.summary || "",
      }));
    } catch (error) {
      console.error("Failed to fetch Knowledge:", error);
      knowledgeError = "Failed to load Knowledge options. Please try again.";
    } finally {
      loadingKnowledge = false;
    }
  }

  // Handle tool selection/deselection
  function handleToolChange(toolId: string, isChecked: boolean) {
    if (isChecked) {
      $wizardSelectedTools = [...$wizardSelectedTools, toolId];
    } else {
      $wizardSelectedTools = $wizardSelectedTools.filter((id) => id !== toolId);
    }
  }

  // Handle knowledge selection/deselection
  function handleKnowledgeChange(knowledgeId: string, isChecked: boolean) {
    if (isChecked) {
      $wizardSelectedKnowledge = [...$wizardSelectedKnowledge, knowledgeId];
    } else {
      $wizardSelectedKnowledge = $wizardSelectedKnowledge.filter(
        (id) => id !== knowledgeId,
      );
    }
  }

  // Global keyboard handler for wizard navigation
  function handleKeydown(event: KeyboardEvent) {
    // Handle Enter key
    if (event.key === "Enter") {
      const target = event.target as HTMLElement;

      // For textarea, only submit on Ctrl+Enter or Cmd+Enter
      if (target.tagName === "TEXTAREA") {
        if (event.ctrlKey || event.metaKey) {
          event.preventDefault();
          nextStep();
        }
        return;
      }

      // For all other inputs, Enter advances to next step
      event.preventDefault();
      nextStep();
    }
  }

  onMount(() => {
    // Initialize current step if not already set
    if (!$wizardActiveStep) {
      $wizardActiveStep = 1;
    }

    // Fetch LLMs, Tools, and Knowledge when component mounts
    fetchLlms();
    fetchTools();
    fetchKnowledge();
  });
</script>

<div
  class="container mx-auto px-4 py-8 max-w-4xl border-2 border-green-600"
  on:keydown={handleKeydown}
>
  <h1 class="text-2xl font-bold mb-6 text-center text-gray-900 dark:text-gray-200">
    Project Setup Wizard
  </h1>

  <div class="mb-8">
    <StepIndicator color="purple" currentStep={$wizardActiveStep} {steps} />
  </div>

  <div
    class="bg-white p-6 rounded-lg shadow-md dark:bg-gray-900 dark:text-white max-h-[70vh] overflow-y-auto"
  >
    {#if $wizardActiveStep === 1}
      <div class="space-y-4">
        <h2 class="text-xl font-semibold text-gray-900 dark:text-white">Enter Branch Name</h2>
        <div>
          <Label for="branch-name" class="text-gray-900 dark:text-gray-200">Branch Name</Label>
          <Input
            id="branch-name"
            placeholder="Enter branch name"
            bind:value={$wizardBranchName}
            class="focus:ring-0 focus:border-gray-300 focus:outline-none"
          />
          <p class="text-sm text-gray-500 mt-1">
            {$wizardBranchName?.length || 0}/50 characters
          </p>

          <!-- Debug info (remove in production) -->
          {#if $wizardBranchName}
            <p class="text-xs text-blue-500 mt-1">
              Current value: "{$wizardBranchName}"
            </p>
          {/if}
        </div>
      </div>
    {:else if $wizardActiveStep === 2}
      <div class="space-y-4">
        <h2 class="text-xl font-semibold">Select Git Repositories</h2>
        <GitMultiSelect on:selectionchange={handleRepoSelect} />
      </div>
    {:else if $wizardActiveStep === 3}
      <div class="space-y-4">
        <h2 class="text-xl font-semibold">Choose LLM Model</h2>
        <div>
          <Label for="llm-select">Select LLM</Label>
          {#if loadingLlms}
            <div class="flex items-center gap-2">
              <Spinner size="4" />
              <span>Loading LLM options...</span>
            </div>
          {:else if llmError}
            <p class="text-red-600">{llmError}</p>
            <Button class="mt-2" size="sm" on:click={fetchLlms}
              >Try Again</Button
            >
          {:else if llmOptions.length === 0}
            <p class="text-gray-600">No LLM options available</p>
          {:else}
            <Select
              id="llm-select"
              items={llmOptions}
              bind:value={$wizardSelectedLlm}
            />
          {/if}
        </div>
      </div>
    {:else if $wizardActiveStep === 4}
      <div class="space-y-4 h-[500px] overflow-scroll">
        <h2 class="text-xl font-semibold">Select Tools</h2>
        <div>
          <Label>Available Tools</Label>
          {#if loadingTools}
            <div class="flex items-center gap-2">
              <Spinner size="4" />
              <span>Loading Tool options...</span>
            </div>
          {:else if toolsError}
            <p class="text-red-600">{toolsError}</p>
            <Button class="mt-2" size="sm" on:click={fetchTools}
              >Try Again</Button
            >
          {:else if toolOptions.length === 0}
            <p class="text-gray-600">No Tool options available</p>
          {:else}
            <div class="grid gap-2 mt-2">
              {#each toolOptions as tool}
                <div class="flex items-start border p-3 rounded">
                  <Checkbox
                    id={`tool-${tool.value}`}
                    checked={$wizardSelectedTools.includes(tool.value)}
                    on:change={(e) =>
                      handleToolChange(tool.value, e.currentTarget.checked)}
                  />
                  <Label for={`tool-${tool.value}`} class="ml-2 flex flex-col">
                    <span class="font-medium">{tool.name}</span>
                    {#if tool.description}
                      <span class="text-sm text-gray-600"
                        >{tool.description}</span
                      >
                    {/if}
                  </Label>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {:else if $wizardActiveStep === 5}
      <div class="space-y-4 h-[500px] overflow-scroll">
        <h2 class="text-xl font-semibold">Select Knowledge</h2>
        <div>
          <Label>Available Knowledge</Label>
          {#if loadingKnowledge}
            <div class="flex items-center gap-2">
              <Spinner size="4" />
              <span>Loading Knowledge options...</span>
            </div>
          {:else if knowledgeError}
            <p class="text-red-600">{knowledgeError}</p>
            <Button class="mt-2" size="sm" on:click={fetchKnowledge}
              >Try Again</Button
            >
          {:else if knowledgeOptions.length === 0}
            <p class="text-gray-600">No Knowledge options available</p>
          {:else}
            <div class="grid gap-2 mt-2">
              {#each knowledgeOptions as knowledge}
                <div class="flex items-start border p-3 rounded">
                  <Checkbox
                    id={`knowledge-${knowledge.value}`}
                    checked={$wizardSelectedKnowledge.includes(knowledge.value)}
                    on:change={(e) =>
                      handleKnowledgeChange(
                        knowledge.value,
                        e.currentTarget.checked,
                      )}
                  />
                  <Label
                    for={`knowledge-${knowledge.value}`}
                    class="ml-2 flex flex-col"
                  >
                    <span class="font-medium">{knowledge.name}</span>
                    {#if knowledge.summary}
                      <span class="text-sm text-gray-600"
                        >{knowledge.summary}</span
                      >
                    {/if}
                  </Label>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      </div>
    {:else if $wizardActiveStep === 6}
      <div class="space-y-4">
        <h2 class="text-xl font-semibold">Project Description</h2>
        <div>
          <Label for="description">Describe what you want to do</Label>
          <Textarea
            id="description"
            rows={5}
            placeholder="Enter a detailed description of what you want to accomplish..."
            bind:value={$wizardDescription}
          />
          <p class="text-sm text-gray-500 mt-1">
            Press Ctrl+Enter (or Cmd+Enter) to finish
          </p>
        </div>
      </div>
    {/if}

    {#if missionError}
      <div
        class="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg dark:bg-red-900/20 dark:border-red-800"
      >
        <div class="flex items-start">
          <svg
            class="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
              clip-rule="evenodd"
            />
          </svg>
          <div class="ml-3 flex-1">
            <h3 class="text-sm font-medium text-red-800 dark:text-red-300">
              Error
            </h3>
            <p class="mt-1 text-sm text-red-700 dark:text-red-400">
              {missionError}
            </p>
            {#if missionError.includes("Authentication")}
              <p class="mt-2 text-sm text-red-600 dark:text-red-400">
                Try refreshing the page and logging in again, or contact support
                if the issue persists.
              </p>
            {/if}
          </div>
          <button
            on:click={() => (missionError = null)}
            class="ml-3 text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
          >
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clip-rule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>
    {/if}

    <div class="flex justify-between mt-8">
      <Button
        color="light"
        on:click={prevStep}
        disabled={$wizardActiveStep === 1}>Previous</Button
      >

      {#if isNavigating}
        <Button disabled>
          <div class="flex items-center gap-2">
            <Spinner size="4" color="white" />
            <span>Please wait...</span>
          </div>
        </Button>
      {:else}
        <Button class="bg-theme-primary" on:click={nextStep}
          >{$wizardActiveStep === totalSteps ? "Finish" : "Next"}</Button
        >
      {/if}
    </div>
  </div>
</div>

{#if isNavigating}
  <div
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
  >
    <div class="bg-white p-8 rounded-lg shadow-xl flex flex-col items-center">
      <Spinner size="10" color="blue" />
      <p class="mt-4 text-lg font-medium">Setting up your project...</p>
      <p class="text-gray-600 mt-2">Please wait while we prepare everything</p>
    </div>
  </div>
{/if}

<style>
  /* Remove orange focus rings from wizard inputs */
  :global(input:focus),
  :global(select:focus),
  :global(textarea:focus) {
    outline: none !important;
    --tw-ring-color: transparent !important;
    --tw-ring-offset-width: 0 !important;
    --tw-ring-offset-color: transparent !important;
    --tw-ring-offset-shadow: none !important;
    --tw-ring-shadow: none !important;
    box-shadow: none !important;
    border-color: #d1d5db !important; /* Set a neutral border color */
  }

  /* Remove specific overrides from the flowbite components */
  :global(.flowbite-input.focus\:ring-theme-primary:focus),
  :global(.flowbite-input.focus\:ring-primary-500:focus),
  :global(.flowbite-input.focus\:ring-blue-500:focus) {
    --tw-ring-color: transparent !important;
    box-shadow: none !important;
  }
</style>
