<script lang="ts">
  import { Button, Label, Modal } from "flowbite-svelte";

  export let open: boolean;
  export let itemName: string;
  export let onDeleteConfirm: (event: Event) => void;
  export let title: string = "Are you sure you want to delete this item?";
  export let buttonText: string = "Delete";
  export let buttonClass: string = "bg-red-600 hover:bg-red-700";

  function handleDeleteConfirmation(event: Event) {
    event.preventDefault();
    onDeleteConfirm(event);
  }
</script>

<Modal bind:open size="xs" autoclose={false} class="w-full">
  <form class="flex flex-col space-y-6" on:submit={handleDeleteConfirmation}>
    <h3 class="m-4 text-xl font-medium text-gray-900 dark:text-white">
      {title}
    </h3>
    <Label class="space-y-2 text-center font-bold">
      <span>{itemName}</span>
    </Label>
    <Button
      type="submit"
      id="test-delete-confirmation-btn"
      class="w-full {buttonClass}"
    >
      {buttonText}
    </Button>
  </form>
</Modal>
