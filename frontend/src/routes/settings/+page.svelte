<script lang="ts">
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";
  import SettingsModal from "$components/modals/SettingsModal.svelte";

  let isOpen = true;

  function handleClose() {
    // Navigate back or to home when modal is closed
    goto(`${base}/sse-chat`);
  }
</script>

<section class="h-full w-full bg-gray-100 dark:bg-gray-900">
  <SettingsModal bind:isOpen on:close={handleClose} />
</section>
