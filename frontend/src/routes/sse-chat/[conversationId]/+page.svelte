<script lang="ts">
  import SSEChat from "$components/chat/SSEChat.svelte";
  import Missions from "$components/mission/Missions.svelte";
  import { page } from "$app/state";

  // Default title
  let chatTitle = `Chat:${page.params.conversationId}`;
</script>

<div class="flex flex-col h-full overflow-hidden">
  <div class="w-full">
    <Missions />
  </div>
  <div class="flex-grow overflow-hidden">
    <SSEChat conversationTitle={chatTitle} class="h-full" />
  </div>
</div>
