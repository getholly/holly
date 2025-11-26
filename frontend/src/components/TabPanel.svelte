<script lang="ts">
  export let show = false;
</script>

<div class={$$props.class}>
  {#if show}
    <slot></slot>
  {/if}
</div>
