<script lang="ts">
  import { Button, Modal } from "flowbite-svelte";
  import { ExclamationCircleOutline } from "flowbite-svelte-icons";
  import { goto } from "$app/navigation";
  import { routes } from "$lib/routes";
  import { popupModalRelogin } from "$lib/store/auth/tokens.store";

  function relogin() {
    $popupModalRelogin = false;
    goto(routes.logout.path);
  }
</script>

<Modal bind:open={$popupModalRelogin} size="xs" autoclose>
  <div class="text-center">
    <ExclamationCircleOutline
      class="mx-auto mb-4 h-12 w-12 text-gray-400 dark:text-gray-200"
    />
    <h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
      Your login has expired, please click to login again.
    </h3>
    <Button class="bg-theme-primary hover:bg-theme-secondary" on:click={relogin}
      >Login</Button
    >
  </div>
</Modal>
