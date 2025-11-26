<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import { ExclamationCircleOutline } from "flowbite-svelte-icons";
  import {
    modalErrorMessage,
    displayErrorMessage,
  } from "$lib/store/error/errorMessage.store";

  function handleToast() {
    $displayErrorMessage = false;
    $modalErrorMessage = "";
  }
</script>

<Modal bind:open={$displayErrorMessage} size="xs" autoclose>
  <div class="text-center">
    <ExclamationCircleOutline
      class="mx-auto mb-4 h-12 w-12 text-gray-400 dark:text-gray-200"
    />
    <h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
      {$modalErrorMessage}
      <span>(check with Backend support)</span>
    </h3>
    <Button color="red" class="me-2" on:click={handleToast}>ok</Button>
  </div>
</Modal>
