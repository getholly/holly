<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import Chat from "./Chat.svelte";
  import {
    chatTitle,
    chatWithTools,
    showChatModal,
  } from "$lib/store/chat/chat.store";
  import { currentContractId } from "$lib/store/contract/contracts.store";

  function closeModal() {
    $showChatModal = false;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape" && showChatModal) {
      closeModal();
    }
  }
</script>

<Modal
  open={$showChatModal}
  size="xl"
  on:close={closeModal}
  on:hide={closeModal}
>
  <div slot="header">
    <button type="button" on:click={() => ($showChatModal = false)}></button>
  </div>
  <div>
    <Chat
      useStore="true"
      contractId={$currentContractId}
      conversationTitle={$chatTitle}
      useTools={$chatWithTools}
    />
  </div>
  <div slot="footer">
    <Button
      type="button"
      class="btn btn-secondary"
      on:click={() => ($showChatModal = false)}
      >Close
    </Button>
  </div>
</Modal>
