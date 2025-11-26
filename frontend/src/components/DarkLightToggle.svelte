<script>
  import { browser } from "$app/environment";

  export let version = "simple"; // 'simple' or 'advanced'

  let darkMode = false;

  if (browser) {
    darkMode =
      localStorage.getItem("color-theme") === "dark" ||
      (!localStorage.getItem("color-theme") &&
        window.matchMedia("(prefers-color-scheme: dark)").matches);

    // Initialize dark mode on page load
    document.documentElement.classList.toggle("dark", darkMode);
  }

  function toggleDarkMode() {
    darkMode = !darkMode;
    if (browser) {
      document.documentElement.classList.toggle("dark", darkMode);
      localStorage.setItem("color-theme", darkMode ? "dark" : "light");
    }
  }

  function setLightMode() {
    darkMode = false;
    if (browser) {
      document.documentElement.classList.toggle("dark", false);
      localStorage.setItem("color-theme", "light");
    }
  }

  function setDarkMode() {
    darkMode = true;
    if (browser) {
      document.documentElement.classList.toggle("dark", true);
      localStorage.setItem("color-theme", "dark");
    }
  }

  // Export darkMode so parent components can use it
  export { darkMode };
</script>

{#if version === "simple"}
  <!-- Simple Version - Single Toggle Button -->
  <button
    class="p-2 rounded-lg dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 duration-700"
    on:click={toggleDarkMode}
  >
    {#if darkMode}
      <svg
        class="w-5 h-5 text-gray-900 dark:text-gray-100"
        fill="currentColor"
        viewBox="0 0 20 20"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
          fill-rule="evenodd"
          clip-rule="evenodd"
        ></path>
      </svg>
    {:else}
      <svg
        class="w-5 h-5 text-gray-900 dark:text-gray-100"
        fill="currentColor"
        viewBox="0 0 20 20"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
        ></path>
      </svg>
    {/if}
  </button>
{:else if version === "advanced"}
  <!-- Advanced Version - Mode Selector with Current Mode Display -->
  <div class="flex gap-3">
    <!-- Mode Selector Buttons -->
    <div class="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1 gap-1">
      <button
        class="flex items-center gap-2 px-3 py-2 rounded-md transition-all duration-200 {!darkMode
          ? 'bg-white dark:bg-gray-700 shadow-sm'
          : 'hover:bg-gray-200 dark:hover:bg-gray-700'}"
        class:text-blue-600={!darkMode}
        class:dark:text-blue-400={!darkMode}
        class:text-gray-600={darkMode}
        class:dark:text-gray-400={darkMode}
        on:click={setLightMode}
      >
        <svg
          class="w-4 h-4"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z"
            fill-rule="evenodd"
            clip-rule="evenodd"
          ></path>
        </svg>
        <span class="text-sm font-medium">Light</span>
      </button>

      <button
        class="flex items-center gap-2 px-3 py-2 rounded-md transition-all duration-200 {darkMode
          ? 'bg-white dark:bg-gray-700 shadow-sm'
          : 'hover:bg-gray-200 dark:hover:bg-gray-700'}"
        class:text-blue-600={darkMode}
        class:dark:text-blue-400={darkMode}
        class:text-gray-600={!darkMode}
        class:dark:text-gray-400={!darkMode}
        on:click={setDarkMode}
      >
        <svg
          class="w-4 h-4"
          fill="currentColor"
          viewBox="0 0 20 20"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z"
          ></path>
        </svg>
        <span class="text-sm font-medium">Dark</span>
      </button>
    </div>
  </div>
{/if}
