<script lang="ts">
  import {
    accessToken,
    refreshToken,
    isAuthenticated,
    userEmail,
    userName,
    avatarUrl,
    loginEmail,
    popupModalRelogin,
  } from "$lib/store/auth/tokens.store";
  import { get } from "svelte/store";

  // Show the component only in development mode
  const isDev = import.meta.env.DEV;

  // Track if the component is expanded or not
  let isExpanded = false;

  function toggleExpand() {
    isExpanded = !isExpanded;
  }

  async function handleRefresh() {}
</script>

{#if isDev}
  <div
    class="fixed bottom-2 right-2 z-50 bg-blue-100 rounded-lg shadow-lg p-2 text-xs max-w-xs overflow-hidden"
  >
    <div class="flex justify-between items-center">
      <button class="font-semibold text-blue-700" on:click={toggleExpand}>
        {isExpanded ? "Hide" : "Show"} Auth Store
      </button>
      <button
        class="bg-blue-500 hover:bg-blue-600 text-white rounded-full px-2 py-1 ml-2 text-xs"
        on:click={handleRefresh}
      >
        Refresh (Values)
      </button>
    </div>

    {#if isExpanded}
      <div
        class="mt-2 p-2 bg-white rounded border border-blue-200 overflow-auto max-h-80"
      >
        <pre class="text-gray-800 whitespace-pre-wrap break-words text-xs">
          {JSON.stringify(
            {
              accessToken: $accessToken,
              refreshToken: $refreshToken,
              isAuthenticated: $isAuthenticated,
              userEmail: $userEmail,
              userName: $userName,
              avatarUrl: $avatarUrl,
              loginEmail: $loginEmail,
              popupModalRelogin: $popupModalRelogin,
            },
            null,
            2,
          )}
        </pre>
      </div>
    {/if}
  </div>
{/if}
