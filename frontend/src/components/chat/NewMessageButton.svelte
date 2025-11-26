<script lang="ts">
  import MsgLog from "$components/chat/MsgLog.svelte";

  export let msgLog: MsgLog | null = null;
</script>

{#if msgLog && !msgLog.autoScroll}
  <div class="">
    <button
      on:click={() => {
        msgLog.scrollToBottom();
      }}
      class=" text-gray-700 bg-gray-100 hover:bg-gray-400 dark:bg-gray-700 dark:hover:bg-gray-800 dark:text-white font-bold py-2 px-4 rounded-full"
    >
      ↓
    </button>
  </div>
{/if}
