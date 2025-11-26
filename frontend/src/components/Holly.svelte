<script lang="ts">
  import { onMount } from "svelte";
  import { userEmail as storeUserEmail } from "$lib/store/auth/tokens.store";

  onMount(() => {
    console.log("[HOLLY-DEBUG] Holly component mounted");
    // console.log("[HOLLY-DEBUG] Django context:", $djangoContext); // djangoContext removed
  });

  // Props passed from Django - now also available from the store
  export let email: string = ""; // Prop for email
  export let csrfToken: string = ""; // Prop for CSRF token
  export let availableLlms: Array<{ id: number; name: string }> = []; // Prop for LLMs

  // Use store values if props are not provided directly for username and email
  // For csrfToken and availableLlms, they must be passed as props if needed,
  // as they are not in the unified auth store.
  $: effectiveEmail = email || $storeUserEmail;
  $: effectiveCsrfToken = csrfToken; // Relies solely on prop
  $: effectiveAvailableLlms = availableLlms; // Relies solely on prop

  // Local state
  let selectedLlm =
    availableLlms && availableLlms.length > 0 ? availableLlms[0].id : null;
  let userPrompt = "";
  let isLoading = false;
  let conversation: [] = [];

  // Handle LLM selection
  function handleLlmChange(event) {
    selectedLlm = event.target.value;
  }

  // Send message to LLM
  async function sendMessage() {
    if (!userPrompt.trim() || !selectedLlm) return;

    isLoading = true;

    try {
      // Add user message to conversation
      conversation = [
        ...conversation,
        {
          role: "user",
          content: userPrompt,
          timestamp: new Date().toISOString(),
        },
      ];

      // Clear input
      const prompt = userPrompt;
      userPrompt = "";

      // In a real implementation, this would call your API
      // For now, we'll simulate a response
      setTimeout(() => {
        conversation = [
          ...conversation,
          {
            role: "assistant",
            content: `Hello,  this is a simulated response from the Holly app. You selected LLM ID: ${selectedLlm}. Your message was: "${prompt}"`,
            timestamp: new Date().toISOString(),
          },
        ];

        isLoading = false;
      }, 1000);
    } catch (error) {
      console.error("Error sending message:", error);
      isLoading = false;
    }
  }
</script>

<div class="flex flex-col h-full bg-theme-surface dark:bg-theme-dark-bg">
  <!-- Header with LLM selection -->
  <div
    class="p-4 border-b border-theme-border dark:border-theme-border-dark bg-theme-light-bg dark:bg-theme-surface-dark"
  >
    <div
      class="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2"
    >
      <h2 class="text-lg font-semibold text-theme-text dark:text-theme-text-inverse">
        Holly AI Assistant
      </h2>

      <div class="flex items-center space-x-2 w-full sm:w-auto">
        <label
          for="llm-selector"
          class="text-sm font-medium text-theme-text-secondary dark:text-theme-text-inverse"
        >
          Select LLM:
        </label>
        <select
          id="llm-selector"
          class="bg-theme-surface border border-theme-border text-theme-text text-sm rounded-lg focus:ring-theme-primary focus:border-theme-primary block p-2 dark:bg-theme-surface-dark dark:border-theme-border-dark dark:text-theme-text-inverse"
          on:change={handleLlmChange}
          value={selectedLlm}
        >
          {#each availableLlms as llm}
            <option value={llm.id}>{llm.name}</option>
          {/each}
        </select>
      </div>
    </div>
  </div>

  <!-- Chat messages -->
  <div
    class="text-center p-4 dark:text-white dark:bg-blue-400 bg-red-300 rounded-xl"
  >
    DEBUG:
    <div>email: {effectiveEmail} (Prop: {email}, Store: {$storeUserEmail})</div>
    <div>token: {effectiveCsrfToken} (Prop: {csrfToken})</div>
    <div>
      llms: {JSON.stringify(effectiveAvailableLlms)} (Prop: {JSON.stringify(
        availableLlms,
      )})
    </div>
  </div>

  <div class="flex-1 overflow-y-auto p-4 space-y-4">
    {#if conversation.length === 0}
      <div class="flex justify-center items-center h-32">
        <p class="text-gray-500 dark:text-gray-400 text-center">
          Start a conversation with Holly using the input below.
          <br />
          Choose from available LLMs:
          {#each availableLlms as llm, i}{llm.name}
            {#if i < availableLlms.length - 1},{/if}
          {/each}
        </p>
      </div>
    {:else}
      {#each conversation as message}
        <div
          class={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
        >
          <div
            class={`max-w-3xl rounded-lg p-3 ${
              message.role === "user"
                ? "bg-blue-500 text-white"
                : "bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white"
            }`}
          >
            <p>{message.content}</p>
            <div class="text-xs mt-1 opacity-75 text-right">
              {new Date(message.timestamp).toLocaleTimeString()}
            </div>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Chat input -->
  <div
    class="border-t border-gray-200 dark:border-gray-700 p-4 bg-white dark:bg-gray-900"
  >
    <form
      on:submit|preventDefault={sendMessage}
      class="flex items-center space-x-2"
    >
      <input
        type="text"
        bind:value={userPrompt}
        placeholder="Type your message..."
        class="flex-1 bg-gray-50 border border-gray-300 text-gray-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 p-2.5 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white"
        disabled={isLoading}
      />
      <button
        type="submit"
        class="text-white bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:ring-blue-300 font-medium rounded-lg text-sm px-5 py-2.5 dark:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none dark:focus:ring-blue-800"
        disabled={isLoading || !userPrompt.trim() || !selectedLlm}
      >
        {#if isLoading}
          <span class="inline-block animate-spin mr-2">⟳</span>
          Sending...
        {:else}
          Send
        {/if}
      </button>
    </form>
    <div class="mt-2 text-xs text-gray-500 dark:text-gray-400 text-right">
      Logged in as: ({effectiveEmail})
    </div>
  </div>
</div>
