<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import type { Conversation } from "holly-api";
  import { conversations } from "$lib/store/chat/chat.store";
  import { get } from "svelte/store";

  export let showDeleteModal = false;
  export let conversationToDelete: Conversation | undefined = undefined;

  // TODO: need to correctly implement this to be able to delete conversations
  // function openDeleteModal(conversation: Conversation) {
  //     conversationToDelete = conversation
  //     showDeleteModal = true
  // }

  async function deleteConv() {
    if (conversationToDelete) {
      console.log(`Deleting conversation: ${conversationToDelete.id}`);
      // TODO: need to implement the delete conversation in the backend
      // await deleteConversation(conversationToDelete.id)
      conversations.set(
        get(conversations).filter((c) => c.id !== conversationToDelete?.id),
      );
      showDeleteModal = false;
      //conversationToDelete = null
    }
  }
</script>

<Modal bind:open={showDeleteModal} size="xs" autoclose={false}>
  <div class="text-center">
    <h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
      Are you sure you want to delete this conversation? ({conversationToDelete?.title ||
        conversationToDelete?.id})
    </h3>
    <div class="flex justify-center gap-4">
      <Button color="red" on:click={deleteConv}>Yes, I'm sure</Button>
      <Button color="alternative" on:click={() => (showDeleteModal = false)}>
        No, cancel
      </Button>
    </div>
  </div>
</Modal>
