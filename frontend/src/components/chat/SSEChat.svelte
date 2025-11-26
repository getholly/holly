<script lang="ts">
  import DeleteChatModal from "$components/chat/DeleteChatModal.svelte";
  import SidePanel from "$components/chat/SidePanel.svelte";
  import ChatTabs from "$components/chat/chat_panel/ChatTabs.svelte";
  import { get } from "svelte/store";
  import { currentMission } from "$lib/store/mission/mission.store";
  import SettingsModal from "$components/modals/SettingsModal.svelte";

  export let conversationTitle: string = "";

  // State to track if the sidebar is collapsed
  let isCollapsed = false;

  // State to track if the settings modal is open
  let isSettingsOpen = false;

  // Function to toggle sidebar
  const toggleSidebar = () => {
    isCollapsed = !isCollapsed;
  };

  // Function to open settings modal
  const openSettings = () => {
    isSettingsOpen = true;
  };

  // Function to close settings modal
  const closeSettings = () => {
    isSettingsOpen = false;
  };

  $: console.log(`$currentMission: ${get(currentMission)}`);
</script>

<div class="flex flex-col-2 h-full w-full {$$props.class}">
  <!-- Side panel with dynamic width based on collapse state -->
  <div
    class="{isCollapsed
      ? 'w-12'
      : 'w-1/3'} transition-all duration-300 ease-in-out flex flex-col relative h-full bg-gray-50 dark:bg-gray-800 border-r border-gray-300 dark:border-gray-700 shadow-lg"
  >
    <!-- Only show content when not collapsed -->
    <div class="{isCollapsed ? 'hidden' : 'block'} p-4 flex-grow relative">
      <SidePanel />

      <!-- Settings button at the bottom -->
      <div
        class="absolute bottom-2 left-4 right-4 border-t dark:border-gray-800"
      >
        <button
          class="w-full px-4 py-2 bg-transparent hover:bg-gray-200 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-md transition-colors duration-200 flex items-center justify-center space-x-2"
          on:click={openSettings}
        >
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
          </svg>
          <span>Settings</span>
        </button>
      </div>
    </div>

    <!-- Toggle button with dynamic positioning -->
    <button
      class="absolute {isCollapsed
        ? 'right-1 top-4'
        : 'right-0 top-6'} border-0 rounded-full p-1 z-10 hover:bg-gray-100 dark:hover:bg-gray-900 bg-transparent p-2 opacity-50"
      on:click={toggleSidebar}
      aria-label={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
    >
      {#if isCollapsed}
        <img
          src="img/sidebar-icon.webp"
          alt="sidebar Icon"
          class="invert dark:invert-0"
        />
      {:else}
        <img
          src="img/close-sidebar-icon.webp"
          alt="Close sidebar Icon"
          class="invert dark:invert-0 w-6"
        />
      {/if}
    </button>
  </div>

  <!-- Main content that expands when sidebar collapses -->
  <div class="w-full h-full flex flex-col bg-theme-light-bg dark:bg-theme-dark-bg">
    <ChatTabs {conversationTitle} />
  </div>

  <!-- Modals -->
  <DeleteChatModal />
  <SettingsModal bind:isOpen={isSettingsOpen} on:close={closeSettings} />
</div>
