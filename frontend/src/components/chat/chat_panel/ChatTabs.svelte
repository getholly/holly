<script lang="ts">
  import ChatConversation from "$components/chat/chat_panel/ChatConversation.svelte";

  export let conversationTitle: string = "";
</script>

<!-- Simplified - just the conversation without tabs -->
<div
  class="h-full flex flex-col bg-transparent dark:bg-transparent {$$props.class}"
>
  <div class="flex-1 h-full">
    <div class="h-full flex">
      <ChatConversation {conversationTitle} class="flex flex-col w-full" />
    </div>
  </div>
</div>
