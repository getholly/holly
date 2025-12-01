<script lang="ts">
  import SSEChat from "$components/chat/SSEChat.svelte";
  import { page } from "$app/state";

  // Default title
  let chatTitle = `Chat:${page.params.conversationId}`;
</script>

<div class="flex flex-col h-full overflow-hidden">
  <div class="flex-grow overflow-hidden">
    <SSEChat conversationTitle={chatTitle} class="h-full" />
  </div>
</div>
