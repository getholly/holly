<script lang="ts">
  import { goto } from "$app/navigation";
  import { Card } from "flowbite-svelte";
  import { base } from "$app/paths";
  import { navigateToAdvanced } from "$components/index";

  function navigateToWizard() {
    goto(`${base}/wizard`);
  }

  function navigateToGitHubConnect() {
    goto(`${base}/github/connect`);
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-12 p-4 md:p-6">
  <Card
    class="cursor-pointer hover:shadow-lg transition-all transform hover:scale-105 dark:bg-gray-900"
    padding="xl"
    on:click={navigateToWizard}
  >
    <div class="flex flex-col items-center text-center">
      <h2
        class="text-2xl md:text-3xl font-bold mb-3 md:mb-4 dark:text-gray-200"
      >
        Wizard
      </h2>
      <p class="text-gray-600 dark:text-gray-300 text-sm md:text-base">
        Use our step-by-step wizard to set up your project
      </p>
      <div class="mt-5 md:mt-6">
        <svg
          class="w-12 h-12 md:w-16 md:h-16 mx-auto text-blue-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
          ></path>
        </svg>
      </div>
    </div>
  </Card>

  <Card
    class="cursor-pointer hover:shadow-lg transition-all transform hover:scale-105 dark:bg-gray-900"
    padding="xl"
    on:click={navigateToAdvanced}
  >
    <div class="flex flex-col items-center text-center">
      <h2
        class="text-2xl md:text-3xl font-bold mb-3 md:mb-4 dark:text-gray-200"
      >
        Advanced
      </h2>
      <p class="text-gray-600 dark:text-gray-300 text-sm md:text-base">
        Access advanced features and configuration options
      </p>
      <div class="mt-5 md:mt-6">
        <svg
          class="w-12 h-12 md:w-16 md:h-16 mx-auto text-purple-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          ></path>
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          ></path>
        </svg>
      </div>
    </div>
  </Card>

  <Card
    class="cursor-pointer hover:shadow-lg transition-all transform hover:scale-105 dark:bg-gray-900"
    padding="xl"
    on:click={navigateToGitHubConnect}
  >
    <div class="flex flex-col items-center text-center">
      <h2
        class="text-2xl md:text-3xl font-bold mb-3 md:mb-4 dark:text-gray-200"
      >
        Connect GitHub
      </h2>
      <p class="text-gray-600 dark:text-gray-300 text-sm md:text-base">
        Link your GitHub account to manage repositories
      </p>
      <div class="mt-5 md:mt-6">
        <svg
          class="w-12 h-12 md:w-16 md:h-16 mx-auto text-green-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"
          ></path>
        </svg>
      </div>
    </div>
  </Card>
</div>
