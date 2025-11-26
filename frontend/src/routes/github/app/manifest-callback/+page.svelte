<script lang="ts">
  import { onMount } from "svelte";
  import { browser } from "$app/environment";

  let code: string | null = null;
  let copied = false;
  let errorMessage = "";

  onMount(() => {
    if (!browser) return;

    const urlParams = new URLSearchParams(window.location.search);
    const codeParam = urlParams.get("code");

    if (!codeParam) {
      errorMessage = "No code parameter found in URL. App creation may have failed.";
      return;
    }

    code = codeParam;
  });

  async function copyToClipboard() {
    if (!code || !browser) return;

    try {
      await navigator.clipboard.writeText(code);
      copied = true;
      setTimeout(() => {
        copied = false;
      }, 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
      alert("Failed to copy to clipboard. Please copy manually.");
    }
  }
</script>

<svelte:head>
  <title>GitHub App Created - Holly</title>
</svelte:head>

<div class="container mx-auto p-4 max-w-2xl">
  <div class="bg-white dark:bg-gray-800 shadow-md rounded px-8 pt-6 pb-8 mb-4">
    <h1
      class="text-2xl font-bold mb-6 text-center text-gray-900 dark:text-white"
    >
      GitHub App Created Successfully!
    </h1>

    {#if code}
      <div class="space-y-4">
        <!-- Success Icon -->
        <div class="flex justify-center mb-4">
          <svg
            class="w-16 h-16 text-green-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
        </div>

        <!-- Instructions -->
        <div class="bg-blue-50 dark:bg-blue-900 border border-blue-200 dark:border-blue-700 rounded-lg p-4 mb-4">
          <h2 class="text-lg font-semibold text-blue-900 dark:text-blue-100 mb-2">
            Next Step
          </h2>
          <p class="text-blue-800 dark:text-blue-200 mb-2">
            Copy the code below and paste it into your terminal when prompted by the setup script.
          </p>
        </div>

        <!-- Code Display with Copy Button -->
        <div class="space-y-2">
          <p class="block text-sm font-medium text-gray-700 dark:text-gray-300">
            Your Manifest Code:
          </p>

          <div class="relative">
            <div class="bg-gray-100 dark:bg-gray-900 border border-gray-300 dark:border-gray-600 rounded-lg p-4 pr-24">
              <code class="text-sm font-mono text-gray-900 dark:text-gray-100 break-all">
                {code}
              </code>
            </div>

            <button
              on:click={copyToClipboard}
              class="absolute top-2 right-2 px-4 py-2 rounded transition duration-150 ease-in-out {copied
                ? 'bg-green-500 hover:bg-green-600'
                : 'bg-blue-500 hover:bg-blue-600'} text-white font-medium text-sm"
            >
              {#if copied}
                <span class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path>
                  </svg>
                  Copied!
                </span>
              {:else}
                <span class="flex items-center gap-2">
                  <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                  </svg>
                  Copy
                </span>
              {/if}
            </button>
          </div>
        </div>

        <!-- Additional Info -->
        <div class="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 mt-6">
          <h3 class="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2">
            What happens next?
          </h3>
          <ol class="list-decimal list-inside space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <li>Return to your terminal</li>
            <li>Paste this code when prompted</li>
            <li>The script will complete your GitHub App configuration</li>
            <li>You'll receive environment variables to add to your <code class="bg-gray-200 dark:bg-gray-600 px-1 rounded">.env</code> file</li>
          </ol>
        </div>

        <!-- Close Window Button -->
        <div class="mt-6 text-center">
          <button
            on:click={() => window.close()}
            class="px-6 py-2 bg-gray-500 hover:bg-gray-600 text-white font-medium rounded transition duration-150 ease-in-out"
          >
            Close This Window
          </button>
        </div>
      </div>
    {:else if errorMessage}
      <div class="text-center py-4">
        <div class="mb-4">
          <svg
            class="w-16 h-16 text-red-500 mx-auto"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            ></path>
          </svg>
        </div>

        <h2 class="text-lg font-semibold text-red-700 dark:text-red-400 mb-2">
          Error
        </h2>
        <p class="text-gray-700 dark:text-gray-300 mb-4">{errorMessage}</p>

        <div class="bg-yellow-50 dark:bg-yellow-900 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4 mt-4">
          <p class="text-sm text-yellow-800 dark:text-yellow-200">
            Return to your terminal and check the setup script output for errors.
          </p>
        </div>
      </div>
    {:else}
      <div class="flex justify-center items-center py-8">
        <div
          class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"
        ></div>
        <p class="ml-4 text-gray-700 dark:text-gray-300">Loading...</p>
      </div>
    {/if}
  </div>
</div>
