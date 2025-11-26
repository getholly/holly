<script lang="ts">
  // Import the original Flowbite Input
  import { Input } from "flowbite-svelte";

  // Forward all props to the underlying Input component
  export let id = undefined;
  export let placeholder = undefined;
  export let value = undefined;
  export let type = "text";
  export let size = "md";
  export let disabled = false;
  export let required = false;
  export let readonly = false;
  export let customClass = ""; // Renamed from class to customClass
  export let override = ""; // We'll ignore this and remove focus rings

  // Add any other props you need to forward
</script>

<!-- Wrap with a div for custom styling -->
<div class="custom-input-wrapper">
  <Input
    {id}
    {placeholder}
    bind:value
    {type}
    {size}
    {disabled}
    {required}
    {readonly}
    class={`${customClass} no-focus-ring`}
    override=""
    {...$$restProps}
  />
</div>

<style>
  /* Override focus styles */
  :global(.custom-input-wrapper input:focus) {
    outline: none !important;
    --tw-ring-color: transparent !important;
    --tw-ring-offset-width: 0 !important;
    --tw-ring-offset-color: transparent !important;
    --tw-ring-offset-shadow: none !important;
    --tw-ring-shadow: none !important;
    box-shadow: none !important;
    border-color: #d1d5db !important;
  }

  :global(.no-focus-ring:focus) {
    outline: none !important;
    --tw-ring-color: transparent !important;
    --tw-ring-offset-width: 0 !important;
    box-shadow: none !important;
  }
</style>
