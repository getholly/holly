<script lang="ts">
  import { goto } from "$app/navigation";
  import { base } from "$app/paths";
  import {
    avatarUrl,
    userEmail,
    isAuthenticated,
  } from "$lib/store/auth/tokens.store";

  function navigate(path: string) {
    goto(`${base}${path}`);
  }
</script>

<div class="space-y-6">
  <div>
    <h4 class="text-lg font-medium text-gray-900 dark:text-white mb-2">
      Account Settings
    </h4>
    <p class="text-gray-600 dark:text-gray-400">
      Manage your account preferences.
    </p>
  </div>

  {#if $isAuthenticated}
    <div class="space-y-4">
      <p class="text-gray-600 dark:text-gray-300">Currently signed in as:</p>
      <div class="flex items-center gap-4">
        <div
          class="bg-gray-100 dark:bg-gray-700 px-4 py-3 rounded-md flex gap-4 items-center"
        >
          {#if $avatarUrl}
            <img
              src={$avatarUrl}
              alt="User Avatar"
              class="h-10 w-10 rounded-full object-cover border-2 border-gray-200 dark:border-gray-600"
            />
          {:else}
            <div
              class="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-medium"
            >
              {$userEmail ? $userEmail.slice(0, 1).toUpperCase() : "?"}
            </div>
          {/if}
          <span class="text-gray-900 dark:text-white font-medium">
            {$userEmail || "Unknown"}
          </span>
        </div>
      </div>

      <div class="pt-4">
        <button
          class="px-4 py-2 text-sm bg-red-600 hover:bg-red-700 rounded-md text-white transition-colors duration-200"
          on:click={() => navigate("/_accounts/logout/")}
        >
          Sign out
        </button>
      </div>
    </div>
  {:else}
    <p class="text-gray-600 dark:text-gray-400">
      You're not currently signed in.
    </p>
  {/if}
</div>
