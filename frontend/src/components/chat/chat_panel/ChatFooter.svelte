<script lang="ts">
  import Mic from "$components/chat/Mic.svelte";
  import { Button, Input } from "flowbite-svelte";
  import { TrashBinOutline } from "flowbite-svelte-icons";
  import { createEventDispatcher } from "svelte";
  import { prompt } from "$lib/store/chat/chat.store";

  const dispatch = createEventDispatcher();
  export let isChatLoading = false;

  let textareaElement;

  // Reactive variable to check if there's text
  $: hasText = $prompt.trim().length > 0;

  function autoResize(event) {
    const textarea = event.target;
    textarea.style.height = "auto";
    textarea.style.height = textarea.scrollHeight + "px";
  }

  function resetTextareaHeight() {
    if (textareaElement) {
      textareaElement.style.height = "auto";
      textareaElement.style.height = "4.5rem"; // Reset to min-height
    }
  }

  function handleSendChatMessage() {
    dispatch("sendChatMessage");
    // Reset textarea height after sending message
    setTimeout(() => {
      resetTextareaHeight();
    }, 0);
  }

  function handleClearChat() {
    dispatch("clearChat");
    // Reset textarea height after clearing
    setTimeout(() => {
      resetTextareaHeight();
    }, 0);
  }

  function handleKeyPress(event) {
    // Check if Enter is pressed without Shift
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault(); // Prevent new line
      if ($prompt.trim() !== "") {
        handleSendChatMessage();
      }
      return;
    }

    dispatch("keyPress", { event });
    autoResize(event);
  }

  function handleInput(event) {
    autoResize(event);
  }

  // Watch for prompt changes (when it gets cleared after sending)
  $: if ($prompt === "") {
    resetTextareaHeight();
  }
</script>

<div
  class="flex w-full align-bottom items-center bg-white dark:bg-transparent border border-gray-300 dark:border-gray-600 rounded-lg"
>
  <div class="flex-grow relative w-full">
    <textarea
      id="tutorInput"
      placeholder="Hello, how may I help you?"
      bind:value={$prompt}
      bind:this={textareaElement}
      class="block border-0 w-full disabled:cursor-not-allowed disabled:opacity-50 rtl:text-right py-2 pr-6 focus:ring-primary-500 dark:focus:ring-primary-500 text-gray-900 bg-transparent dark:text-white dark:placeholder-gray-400 border text-sm rounded-lg focus:ring-0 focus:outline-none focus:border-gray-500 dark:focus:border-gray-100 resize-none min-h-[4.5rem] max-h-[40vh] overflow-y-auto whitespace-pre-wrap break-words"
      on:keypress={handleKeyPress}
      on:input={handleInput}
      rows="2"
    />
  </div>
  <div class="bg-light-grey p-3 rounded flex gap-2 items-center">
    {#if hasText}
      <button
        class=" text-gray-700 hover:text-gray-600 rounded-full p-1 bg-gray-200 dark:bg-gray-900 dark:text-gray-300 dark:hover:text-gray-300 transition-colors duration-200 w-6 h-6 flex items-center justify-center"
        on:click={handleClearChat}
        aria-label="Clear text"
      >
        <svg
          class="w-8 h-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    {/if}
    <Mic on:sendChatMessage={handleSendChatMessage} />
    <Button
      class="bg-theme-primary hover:bg-theme-secondary focus-within:ring-0 duration-300 dark:text-gray-100 dark:bg-theme-primary dark:hover:bg-theme-primary dark:hover:text-gray-100 dark:focus-within:ring-theme-primary"
      on:click={handleSendChatMessage}
      disabled={isChatLoading}
    >
      <!-- Arrow icon for mobile, hidden on md and up -->
      <svg
        class="w-4 h-4 md:hidden"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"
        />
      </svg>
      <!-- Text for larger screens, hidden on mobile -->
      <span class="hidden md:inline">Send</span>
    </Button>
  </div>
</div>
