<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import {
    FileCopyOutline,
    ShareNodesOutline,
    ThumbsUpOutline,
    RefreshOutline,
  } from "flowbite-svelte-icons";
  import { copyToClipboard } from "$lib/utils/clipboard";

  /**
   * The text content to copy
   */
  export let text: string = "";

  /**
   * The role of the message (user or assistant)
   */
  export let role: string = "user";

  // Internal state
  let liked = false;
  let disliked = false;
  let copied = false;

  const dispatch = createEventDispatcher();

  // Reset copied state after a delay
  $: if (copied) {
    setTimeout(() => {
      copied = false;
    }, 2000);
  }

  async function handleCopy() {
    const success = await copyToClipboard(text);
    copied = success;

    dispatch("copy", { success });
  }

  function handleRetry() {
    dispatch("retry");
  }

  function handleShare() {
    dispatch("share");
  }

  function handleLike() {
    if (disliked) disliked = false;
    liked = !liked;
    dispatch("feedback", { liked: true });
  }

  function handleDislike() {
    if (liked) liked = false;
    disliked = !disliked;
    dispatch("feedback", { liked: false });
  }
</script>

<div
  class="flex items-center justify-end gap-2 pt-2 text-gray-500 dark:text-gray-400"
>
  <button
    class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
    class:text-green-500={copied}
    on:click={handleCopy}
    title="Copy message"
  >
    <FileCopyOutline size="sm" />
  </button>

  {#if role === "assistant"}
    <button
      class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
      on:click={handleRetry}
      title="Regenerate response"
    >
      <RefreshOutline size="sm" />
    </button>
  {/if}

  <button
    class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
    on:click={handleShare}
    title="Share message"
  >
    <ShareNodesOutline size="sm" />
  </button>

  <button
    class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
    class:text-green-500={liked}
    on:click={handleLike}
    title="Like"
  >
    <ThumbsUpOutline size="sm" />
  </button>

  <button
    class="p-1 rounded hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
    class:text-red-500={disliked}
    on:click={handleDislike}
    title="Dislike"
  >
    <ThumbsUpOutline size="sm" />
  </button>
</div>
