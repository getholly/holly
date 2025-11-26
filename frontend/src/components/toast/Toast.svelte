<script lang="ts">
  import { _ } from "svelte-i18n";
  import { fly } from "svelte/transition";
  import {
    CheckCircleSolid,
    ExclamationCircleSolid,
    FireOutline,
    CloseCircleSolid,
  } from "flowbite-svelte-icons";
  import { type Toast, toastStore } from "$lib/store/toast/toast.store";

  function removeToast(id: number): void {
    toastStore.removeToast(id);
  }

  function getIconForType(type: Toast["type"]) {
    switch (type) {
      case "success":
        return CheckCircleSolid;
      case "error":
        return CloseCircleSolid;
      case "warning":
        return FireOutline;
      case "info":
        return ExclamationCircleSolid;
      default:
        return ExclamationCircleSolid;
    }
  }

  function getColorForType(type: Toast["type"]) {
    switch (type) {
      case "success":
        return "bg-green-500";
      case "error":
        return "bg-red-500";
      case "warning":
        return "bg-yellow-500";
      case "info":
        return "bg-blue-500";
      default:
        return "bg-gray-500";
    }
  }
</script>

<div class="fixed top-5 right-5 z-50 space-y-2 w-72">
  {#each $toastStore as toast (toast.id)}
    <div
      transition:fly={{ y: -20, duration: 300 }}
      class={`rounded-lg shadow-lg overflow-hidden ${getColorForType(toast.type)}`}
    >
      <div class="px-4 py-3 flex items-center justify-between">
        <div class="flex items-center">
          <svelte:component
            this={getIconForType(toast.type)}
            class="w-5 h-5 mr-2 text-white"
          />
          <p class="text-white font-medium">{toast.message}</p>
        </div>
        <button
          on:click={() => removeToast(toast.id)}
          class="text-white hover:text-gray-200 transition-colors"
        >
          <CloseCircleSolid class="w-5 h-5" />
        </button>
      </div>
    </div>
  {/each}
</div>
