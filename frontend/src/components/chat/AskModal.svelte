<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import Chat from "./Chat.svelte";
  import { showAskModal } from "$lib/store/chat/chat.store";
  import { onMount } from "svelte";

  export let documentId: number;
  export let documentTitle: string;
  export let askWithTools: boolean;

  function closeModal() {
    $showAskModal = false;
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape" && showAskModal) {
      closeModal();
    }
  }
</script>

<Modal
  open={$showAskModal}
  size="xl"
  on:close={closeModal}
  on:hide={closeModal}
  title="Ask about your doc"
>
  <div slot="header">
    <button type="button" on:click={() => ($showAskModal = false)}></button>
  </div>
  <div>
    <Chat
      useStore={false}
      contractId={documentId.toString()}
      conversationTitle={documentTitle}
      useTools={askWithTools}
    />
  </div>
  <div slot="footer">
    <Button
      type="button"
      class="btn btn-secondary"
      on:click={() => ($showAskModal = false)}
      >Close
    </Button>
  </div>
</Modal>
