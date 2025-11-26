<script lang="ts">
  import ConversationHistory from "$components/chat/ConversationHistory.svelte";
</script>

<!-- Just the conversation history without tabs -->
<div class="w-full p-4">
  <div class="mb-4">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
      Conversation History
    </h3>
  </div>
  <ConversationHistory />
</div>
