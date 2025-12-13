<script lang="ts">
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import { routes } from "$lib/routes";
  import { userEmail } from "$lib/store/auth/tokens.store";
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
  <!-- Content -->
  <div class="max-w-7xl mx-auto w-full px-4 py-8 space-y-8">
    <!-- Header -->
    <div
      class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-3"
    >
      <div>
        <h1 class="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-300">
          Welcome{#if $userEmail}, {$userEmail}{/if}
        </h1>
        <p class="text-gray-600 dark:text-gray-400 mt-2 text-lg">
          Quick actions and recent activity
        </p>
      </div>
    </div>

    {#if isLoading}
      <div class="flex items-center gap-3 text-gray-600 dark:text-gray-300 py-12 justify-center">
        <div
          class="animate-spin h-6 w-6 border-t-2 border-b-2 border-blue-500 rounded-full"
        ></div>
        <span class="text-lg">Loading dashboard…</span>
      </div>
    {:else}
      {#if loadError}
        <div class="text-sm text-red-700 bg-red-100 px-3 py-2 rounded">
          {loadError}
        </div>
      {/if}

      <!-- Quick actions -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <a
          href={link("/sse-chat")}
          class="group relative rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
        >
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-cyan-500/10 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
          <div class="flex items-center justify-between relative z-10">
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">
              Chat
            </h3>
            <div class="p-2 bg-blue-50 dark:bg-blue-900/30 rounded-lg group-hover:bg-blue-100 dark:group-hover:bg-blue-900/50 transition-colors">
              <svg
                class="w-6 h-6 text-blue-600 dark:text-blue-400"
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
          </div>
          <p class="mt-4 text-sm text-gray-600 dark:text-gray-400 relative z-10 leading-relaxed">
            Talk to Holly and your code. Continue where you left off.
          </p>
        </a>

        <a
          href={link("/github")}
          class="group relative rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
        >
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-gray-500/10 to-slate-500/10 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
          <div class="flex items-center justify-between relative z-10">
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">
              GitHub
            </h3>
            <div class="p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg group-hover:bg-gray-100 dark:group-hover:bg-gray-700 transition-colors">
              <svg
                class="w-6 h-6 text-gray-700 dark:text-gray-300"
                viewBox="0 0 24 24"
                fill="currentColor"
                ><path
                  d="M12 .5C5.73.5.77 5.46.77 11.74c0 4.93 3.2 9.11 7.64 10.59.56.1.77-.24.77-.54v-2.1c-3.11.68-3.77-1.31-3.77-1.31-.51-1.29-1.25-1.63-1.25-1.63-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 .1 2.07.76 2.47 1.16.1-.74.39-1.25.71-1.54-2.51-.29-5.15-1.25-5.15-5.56 0-1.23.44-2.23 1.16-3.02-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.12 1.16.9-.25 1.86-.38 2.82-.38.96 0 1.92.13 2.82.38 2.17-1.46 3.12-1.16 3.12-1.16.61 1.55.23 2.7.12 2.98.72.79 1.16 1.79 1.16 3.02 0 4.33-2.65 5.26-5.18 5.55.4.34.77 1.02.77 2.06v3.06c0 .31.2.65.78.54 4.42-1.48 7.62-5.66 7.62-10.59C23.23 5.46 18.27.5 12 .5z"
                /></svg
              >
            </div>
          </div>
          <p class="mt-4 text-sm text-gray-600 dark:text-gray-400 relative z-10 leading-relaxed">
            Manage connected repositories and installations.
          </p>
        </a>

        <a
          href={link("/wizard")}
          class="group relative rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
        >
          <div class="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-bl-full -mr-8 -mt-8 transition-transform group-hover:scale-110"></div>
          <div class="flex items-center justify-between relative z-10">
            <h3 class="text-xl font-bold text-gray-900 dark:text-white">
              Wizard
            </h3>
            <div class="p-2 bg-purple-50 dark:bg-purple-900/30 rounded-lg group-hover:bg-purple-100 dark:group-hover:bg-purple-900/50 transition-colors">
              <svg
                class="w-6 h-6 text-purple-600 dark:text-purple-400"
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
          </div>
          <p class="mt-4 text-sm text-gray-600 dark:text-gray-400 relative z-10 leading-relaxed">
            Step-by-step setup to get productive fast.
          </p>
        </a>
      </div>

      <!-- Stats -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <a
          href={link("/missions")}
          class="group rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-cyan-500 dark:hover:border-cyan-500 hover:shadow-lg transition-all cursor-pointer flex flex-col items-center text-center"
        >
          <div class="p-3 rounded-full bg-cyan-50 dark:bg-cyan-900/20 mb-3 group-hover:scale-110 transition-transform duration-300">
            <svg
              class="w-6 h-6 text-cyan-600 dark:text-cyan-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </div>
          <div class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">Missions</div>
          <div class="text-4xl font-bold text-gray-900 dark:text-white mt-1">
            {missionsCount}
          </div>
          <div class="text-xs text-cyan-600 dark:text-cyan-400 mt-2 opacity-0 group-hover:opacity-100 transition-opacity font-medium">
            Manage Missions →
          </div>
        </a>

        <div
          class="rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col items-center text-center"
        >
          <div class="p-3 rounded-full bg-gray-50 dark:bg-gray-700/50 mb-3">
            <svg class="w-6 h-6 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
               <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <div class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            Repositories
          </div>
          <div class="text-4xl font-bold text-gray-900 dark:text-white mt-1">
            {reposCount}
          </div>
        </div>

        <div
          class="rounded-2xl p-6 border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 flex flex-col items-center text-center"
        >
          <div class="p-3 rounded-full bg-green-50 dark:bg-green-900/20 mb-3">
             <svg class="w-6 h-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.985 9.985 0 01-4-.8L3 20l.82-3.28A8.966 8.966 0 013 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
          </div>
          <div class="text-sm font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wide">
            Conversations
          </div>
          <div class="text-4xl font-bold text-gray-900 dark:text-white mt-1">
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
