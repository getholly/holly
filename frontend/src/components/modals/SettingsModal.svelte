<script lang="ts">
  import { createEventDispatcher } from "svelte";

  // Import the extracted components
  import SettingsModalGeneral from "./SettingsModalGeneral.svelte";
  import SettingsModalAppearance from "./SettingsModalAppearance.svelte";
  import SettingsModalLlm from "./SettingsModalLlm.svelte";
  import SettingsModalGithub from "./SettingsModalGithub.svelte";
  import SettingsModelTools from "./SettingsModelTools.svelte";
  import SettingsModalKnowledge from "./SettingsModalKnowledge.svelte";
  import SettingsModalVnc from "./SettingsModalVnc.svelte";
  import SettingsModalAbout from "./SettingsModalAbout.svelte";

  const dispatch = createEventDispatcher();

  export let isOpen = false;

  // Settings menu items
  const menuItems = [
    { id: "general", label: "General" },
    { id: "appearance", label: "Appearance" },
    { id: "llm", label: "Language Model" },
    { id: "github", label: "GitHub Repository" },
    { id: "tools", label: "Tools" },
    { id: "knowledge", label: "Knowledge Base" },
    { id: "vnc", label: "VNC Remote Desktop" },
    { id: "about", label: "About" },
  ];

  let activeSection = "general";

  // Close modal function
  const closeModal = () => {
    isOpen = false;
    dispatch("close");
  };

  // Backdrop click handling removed - modal can only be closed via X button or Escape key

  // Handle escape key
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === "Escape") {
      closeModal();
    }
  };
</script>

<!-- Modal backdrop -->
{#if isOpen}
  <div
    class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
  >
    <!-- Modal container -->
    <div
      class="bg-white dark:bg-gray-800 rounded-lg shadow-xl w-full max-w-4xl h-[80vh] flex overflow-hidden"
      role="dialog"
      aria-modal="true"
      aria-labelledby="settings-title"
    >
      <!-- Left sidebar menu -->
      <div
        class="w-64 bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700 flex flex-col"
      >
        <!-- Header -->
        <div class="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2
            id="settings-title"
            class="text-xl font-semibold text-gray-900 dark:text-white"
          >
            Settings
          </h2>
        </div>

        <!-- Menu items -->
        <nav class="flex-1 p-2">
          {#each menuItems as item}
            <button
              class="w-full text-left px-3 py-2 rounded-md mb-1 flex items-center transition-colors duration-200 {activeSection ===
              item.id
                ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'}"
              on:click={() => (activeSection = item.id)}
            >
              <span class="font-medium">{item.label}</span>
            </button>
          {/each}
        </nav>
      </div>

      <!-- Main content area -->
      <div class="flex-1 flex flex-col">
        <!-- Header with close button -->
        <div
          class="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center"
        >
          <h3
            class="text-lg font-medium text-gray-900 dark:text-white capitalize"
          >
            {menuItems.find((item) => item.id === activeSection)?.label}
          </h3>
          <button
            class="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-full transition-colors duration-200"
            on:click={closeModal}
            aria-label="Close settings"
          >
            <svg
              class="w-5 h-5 text-gray-500 dark:text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <!-- Content area -->
        <div class="flex-1 p-6 overflow-y-auto">
          {#if activeSection === "general"}
            <SettingsModalGeneral />
          {:else if activeSection === "appearance"}
            <SettingsModalAppearance />
          {:else if activeSection === "llm"}
            <SettingsModalLlm />
          {:else if activeSection === "github"}
            <SettingsModalGithub />
          {:else if activeSection === "tools"}
            <SettingsModelTools />
          {:else if activeSection === "knowledge"}
            <SettingsModalKnowledge />
          {:else if activeSection === "vnc"}
            <SettingsModalVnc />
          {:else if activeSection === "about"}
            <SettingsModalAbout />
          {/if}
        </div>

        <!-- Footer with action buttons -->
        <div
          class="p-4 border-t border-gray-200 dark:border-gray-700 flex justify-end space-x-3"
        >
          <button
            class="px-4 py-2 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-md hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors duration-200"
            on:click={closeModal}
          >
            Cancel
          </button>
          <button
            class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors duration-200"
            on:click={closeModal}
          >
            Save Changes
          </button>
        </div>
      </div>
    </div>
  </div>
{/if}

<svelte:window on:keydown={handleKeydown} />
