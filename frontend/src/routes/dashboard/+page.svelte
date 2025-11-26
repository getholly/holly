<script lang="ts">
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { routes } from "$lib/routes";
  import { userEmail } from "$lib/store/auth/tokens.store";
  import Missions from "$components/mission/Missions.svelte";
  import { get } from "svelte/store";
  import { currentMission } from "$lib/store/mission/mission.store";

  import { getMissions } from "$lib/apis/mission/api.mission";
  import { getRepos } from "$lib/apis/github/api.github";
  import { getConversations } from "$lib/apis/conversation/api.conversation";

  let missionsCount = 0;
  let reposCount = 0;
  let conversationsCount = 0;

  let recentConversations: Array<{
    id: string;
    title?: string;
    updated_at?: string;
  }> = [];
  let isLoading = true;
  let loadError = "";

  onMount(async () => {
    try {
      const [missions, repos] = await Promise.all([
        getMissions().catch(() => []),
        getRepos(true).catch(() => []),
      ]);
      missionsCount = missions?.length || 0;
      reposCount = repos?.length || 0;

      // Conversations depend on selected mission
      if (get(currentMission)?.id) {
        const convos = await getConversations().catch(() => []);
        conversationsCount = convos?.length || 0;
        recentConversations = (convos || []).slice(0, 5);
      }
    } catch (e) {
      loadError = "Failed to load dashboard data";
      console.error(e);
    } finally {
      isLoading = false;
    }
  });

  function link(path: string) {
    return `${base}${path}`;
  }
</script>

<svelte:head>
  <title>Dashboard</title>
  <meta name="description" content="Your Holly dashboard" />
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="flex flex-col h-full overflow-auto">
  <!-- Mission bar -->
  <div class="w-full">
    <Missions />
  </div>

  <!-- Content -->
  <div class="max-w-7xl mx-auto w-full px-4 py-6 space-y-6">
    <!-- Header -->
    <div
      class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3"
    >
      <div>
        <h1 class="text-2xl font-semibold text-gray-900 dark:text-white">
          Welcome{#if $userEmail}, {$userEmail}{/if}
        </h1>
        <p class="text-gray-600 dark:text-gray-300">
          Quick actions and recent activity
        </p>
      </div>
    </div>

    {#if isLoading}
      <div class="flex items-center gap-3 text-gray-600 dark:text-gray-300">
        <div
          class="animate-spin h-5 w-5 border-t-2 border-b-2 border-blue-500 rounded-full"
        ></div>
        <span>Loading dashboard…</span>
      </div>
    {:else}
      {#if loadError}
        <div class="text-sm text-red-700 bg-red-100 px-3 py-2 rounded">
          {loadError}
        </div>
      {/if}

      <!-- Quick actions -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href={link("/sse-chat")}
          class="group rounded-xl p-5 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Chat
            </h3>
            <svg
              class="w-6 h-6 text-theme-primary group-hover:scale-110 transition-transform"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M8 10h.01M12 10h.01M16 10h.01M21 12c0 4.418-4.03 8-9 8a9.985 9.985 0 01-4-.8L3 20l.82-3.28A8.966 8.966 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
              /></svg
            >
          </div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Talk to Holly and your code. Continue where you left off.
          </p>
        </a>

        <a
          href={link("/github")}
          class="group rounded-xl p-5 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              GitHub
            </h3>
            <svg
              class="w-6 h-6 text-theme-primary group-hover:scale-110 transition-transform"
              viewBox="0 0 24 24"
              fill="currentColor"
              ><path
                d="M12 .5C5.73.5.77 5.46.77 11.74c0 4.93 3.2 9.11 7.64 10.59.56.1.77-.24.77-.54v-2.1c-3.11.68-3.77-1.31-3.77-1.31-.51-1.29-1.25-1.63-1.25-1.63-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 .1 2.07.76 2.47 1.16.1-.74.39-1.25.71-1.54-2.51-.29-5.15-1.25-5.15-5.56 0-1.23.44-2.23 1.16-3.02-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.12 1.16.9-.25 1.86-.38 2.82-.38.96 0 1.92.13 2.82.38 2.17-1.46 3.12-1.16 3.12-1.16.61 1.55.23 2.7.12 2.98.72.79 1.16 1.79 1.16 3.02 0 4.33-2.65 5.26-5.18 5.55.4.34.77 1.02.77 2.06v3.06c0 .31.2.65.78.54 4.42-1.48 7.62-5.66 7.62-10.59C23.23 5.46 18.27.5 12 .5z"
              /></svg
            >
          </div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Manage connected repositories and installations.
          </p>
        </a>

        <a
          href={link("/wizard")}
          class="group rounded-xl p-5 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-md transition-shadow"
        >
          <div class="flex items-center justify-between">
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Wizard
            </h3>
            <svg
              class="w-6 h-6 text-theme-primary group-hover:scale-110 transition-transform"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              ><path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"
              /></svg
            >
          </div>
          <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">
            Step-by-step setup to get productive fast.
          </p>
        </a>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div
          class="rounded-xl p-4 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        >
          <div class="text-sm text-gray-500 dark:text-gray-400">Missions</div>
          <div class="text-2xl font-semibold text-gray-900 dark:text-white">
            {missionsCount}
          </div>
        </div>
        <div
          class="rounded-xl p-4 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        >
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Repositories
          </div>
          <div class="text-2xl font-semibold text-gray-900 dark:text-white">
            {reposCount}
          </div>
        </div>
        <div
          class="rounded-xl p-4 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        >
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Conversations
          </div>
          <div class="text-2xl font-semibold text-gray-900 dark:text-white">
            {conversationsCount}
          </div>
        </div>
      </div>

      <!-- Recent conversations (if any) -->
      {#if recentConversations.length > 0}
        <div
          class="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800"
        >
          <div
            class="px-5 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between"
          >
            <h3 class="text-lg font-medium text-gray-900 dark:text-white">
              Recent conversations
            </h3>
            <a
              class="text-sm text-theme-primary hover:underline"
              href={link("/sse-chat")}>Open chat</a
            >
          </div>
          <ul class="divide-y divide-gray-200 dark:divide-gray-700">
            {#each recentConversations as c}
              <li class="px-5 py-3">
                <div class="flex items-center justify-between">
                  <div class="truncate">
                    <div
                      class="text-sm font-medium text-gray-900 dark:text-white truncate"
                    >
                      {c.title || "Untitled conversation"}
                    </div>
                    {#if c.updated_at}
                      <div class="text-xs text-gray-500 dark:text-gray-400">
                        Updated {new Date(c.updated_at).toLocaleString()}
                      </div>
                    {/if}
                  </div>
                  <a
                    class="text-sm text-theme-primary hover:underline whitespace-nowrap"
                    href={link("/sse-chat")}>Continue →</a
                  >
                </div>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    {/if}
  </div>
</div>
