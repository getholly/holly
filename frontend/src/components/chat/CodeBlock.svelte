<script lang="ts">
  import { onMount } from "svelte";
  import { FileCopyOutline } from "flowbite-svelte-icons";
  import { copyToClipboard } from "$lib/utils/clipboard";

  /**
   * The HTML element containing code elements to enhance
   */
  export let element: HTMLElement | null = null;

  let codeBlocks: HTMLElement[] = [];
  let copiedIndex: number | null = null;

  onMount(() => {
    if (element) {
      enhanceCodeBlocks();
    }
  });

  $: if (element) {
    enhanceCodeBlocks();
  }

  // When copiedIndex changes, reset it after a delay
  $: if (copiedIndex !== null) {
    setTimeout(() => {
      copiedIndex = null;
    }, 2000);
  }

  function enhanceCodeBlocks() {
    if (!element) return;

    // Find all pre > code elements
    const preElements = element.querySelectorAll("pre");
    codeBlocks = Array.from(preElements);
  }

  async function handleCopy(index: number, pre: HTMLElement) {
    // Get code content
    const code = pre.querySelector("code");
    if (!code) return;

    // Copy text content to clipboard
    const success = await copyToClipboard(code.textContent || "");

    if (success) {
      copiedIndex = index;
    }
  }
</script>

{#if codeBlocks.length > 0}
  {#each codeBlocks as block, index}
    <div class="relative group">
      <button
        class="absolute top-2 right-2 p-1 rounded bg-gray-700 text-white opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
        class:text-green-500={copiedIndex === index}
        on:click={() => handleCopy(index, block)}
        title="Copy code"
      >
        <FileCopyOutline size="sm" />
      </button>
    </div>
  {/each}
{/if}
