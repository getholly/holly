<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import {
    Button,
    Label,
    Input,
    Select,
    Textarea,
    StepIndicator,
  } from "flowbite-svelte";
  import GitMultiSelect from "$components/gitrepo/GitMultiSelect.svelte";
  import type { RepoSelection } from "$lib/types/githubTypes";
  import {
    wizardActiveStep,
    wizardBranchName,
    wizardSelectedRepos,
    wizardSelectedLlm,
    wizardDescription,
  } from "$lib/store/wizard.store";
  import Holly from "$components/Holly.svelte";
  import { base } from "$app/paths";

  // LLM options from API
  import {
    llmModels,
    formatLLMsForDropdown,
    loadLLMs,
  } from "$lib/store/llm/llm.store";

  // Initialize LLM options
  let llmOptions: { value: string; name: string }[] = [];

  // Define steps and totalSteps
  let steps = [
    "Branch Name",
    "Select Repositories",
    "Choose LLM",
    "Project Description",
  ];
  const totalSteps = steps.length;

  function prevStep() {
    if ($wizardActiveStep > 1) {
      $wizardActiveStep = $wizardActiveStep - 1;
    }
  }

  function nextStep() {
    if ($wizardActiveStep < totalSteps) {
      $wizardActiveStep = $wizardActiveStep + 1;
    } else {
      // Final step - navigate to SSE chat
      goto(`${base}/sse-chat`);
    }
  }

  function handleRepoSelect(event: CustomEvent) {
    $wizardSelectedRepos = event.detail;
  }

  // Load LLMs when component mounts
  onMount(async () => {
    // Initialize step
    if (!$wizardActiveStep) {
      $wizardActiveStep = 1;
    }

    // Load LLMs
    await loadLLMs();

    // Update options based on loaded models
    if ($llmModels.length > 0) {
      llmOptions = formatLLMsForDropdown($llmModels);
    } else {
      // Fallback to default options if API request fails
      llmOptions = [
        { value: "gpt-4", name: "GPT-4" },
        { value: "gpt-3.5-turbo", name: "GPT-3.5 Turbo" },
        { value: "claude-3", name: "Claude 3" },
        { value: "llama-3", name: "Llama 3" },
      ];
    }
  });
</script>

<Holly></Holly>
<div class="container mx-auto px-4 py-8 max-w-4xl">
  <h1 class="text-2xl font-bold mb-6 text-center">Project Setup Wizard</h1>

  <div class="mb-8">
    <StepIndicator currentStep={$wizardActiveStep} {steps} glow />
  </div>

  <div class="bg-white p-6 rounded-lg shadow-md">
    {#if $wizardActiveStep === 1}
      <div class="space-y-4">
        <h2 class="text-xl font-semibold">Enter Branch Name</h2>
        <div>
          <Label for="branch-name">Branch Name</Label>
          <Input
            id="branch-name"
            placeholder="Enter branch name"
            bind:value={$wizardBranchName}
          />
          <p class="text-sm text-gray-500 mt-1">
            {$wizardBranchName?.length || 0}/50 characters
          </p>
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
          <Select
            id="llm-select"
            items={llmOptions}
            bind:value={$wizardSelectedLlm}
          />
        </div>
      </div>
    {:else if $wizardActiveStep === 4}
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
        </div>
      </div>
    {/if}

    <div class="flex justify-between mt-8">
      <Button
        color="light"
        on:click={prevStep}
        disabled={$wizardActiveStep === 1}>Previous</Button
      >
      <Button on:click={nextStep}
        >{$wizardActiveStep === totalSteps ? "Finish" : "Next"}</Button
      >
    </div>
  </div>
</div>
