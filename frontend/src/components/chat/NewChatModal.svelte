<script lang="ts">
  import { Modal, Button, Label, Input, Textarea } from "flowbite-svelte";
  import { showToast } from "$lib/store/toast/toast.store";

  export let display = false;
  export let onClose = () => {};
  export let onSubmit = (title: string, message: string) => {};

  let chatTitle = "";
  let initialMessage = "";

  function handleCancel() {
    chatTitle = "";
    initialMessage = "";
    onClose();
  }

  function handleSubmit() {
    if (!chatTitle || chatTitle.trim() === "") {
      showToast("Chat title cannot be empty", "error");
      return;
    }

    onSubmit(chatTitle, initialMessage);
    chatTitle = "";
    initialMessage = "";
    onClose();
  }
</script>

<Modal bind:open={display} size="lg" autoclose={false} class="w-full">
  <div class="p-4">
    <h3 class="mb-5 text-xl font-medium text-gray-900 dark:text-white">
      Start New Chat
    </h3>
    <form on:submit|preventDefault={handleSubmit} class="space-y-4">
      <div>
        <Label for="chat-title" class="mb-2">Chat Title</Label>
        <Input
          id="chat-title"
          placeholder="Enter a title for your chat"
          required
          bind:value={chatTitle}
          class="w-full"
        />
      </div>
      <div>
        <Label for="initial-message" class="mb-2"
          >Initial Message (Optional)</Label
        >
        <Textarea
          id="initial-message"
          placeholder="Enter your first message..."
          rows="4"
          bind:value={initialMessage}
          class="w-full"
        />
      </div>
      <div class="flex justify-end space-x-3 pt-4">
        <Button color="alternative" on:click={handleCancel}>Cancel</Button>
        <Button type="submit" color="blue">Start Chat</Button>
      </div>
    </form>
  </div>
</Modal>
