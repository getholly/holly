<script lang="ts">
  import SSEChat from "$components/chat/SSEChat.svelte";

  // Default title
  let chatTitle = "SSE Chat";
</script>

<div class="flex flex-col h-full overflow-hidden">
  <div class="flex-grow overflow-hidden">
    <SSEChat conversationTitle={chatTitle} class="h-full" />
  </div>
</div>
