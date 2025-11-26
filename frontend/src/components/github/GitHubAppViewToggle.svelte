<script lang="ts">
  import { ViewTypeEnum } from "./ViewTypes";

  export let viewType = ViewTypeEnum.Grid;

  function setViewType(newType) {
    viewType = newType;
  }
</script>

<div class="flex justify-center space-x-4 mb-6">
  <button
    class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md
    {viewType === ViewTypeEnum.Installations
      ? 'text-white bg-indigo-600'
      : 'text-indigo-700 bg-indigo-100 dark:bg-indigo-900 dark:text-indigo-100'}
    hover:bg-indigo-200 dark:hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
    on:click={() => setViewType(ViewTypeEnum.Installations)}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 mr-1"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
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
    Installations
  </button>
  <button
    class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md
    {viewType === ViewTypeEnum.Grid
      ? 'text-white bg-indigo-600'
      : 'text-indigo-700 bg-indigo-100 dark:bg-indigo-900 dark:text-indigo-100'} 
    hover:bg-indigo-200 dark:hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
    on:click={() => setViewType(ViewTypeEnum.Grid)}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 mr-1"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
      />
    </svg>
    Grid
  </button>
  <button
    class="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md
    {viewType === ViewTypeEnum.List
      ? 'text-white bg-indigo-600'
      : 'text-indigo-700 bg-indigo-100 dark:bg-indigo-900 dark:text-indigo-100'} 
    hover:bg-indigo-200 dark:hover:bg-indigo-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
    on:click={() => setViewType(ViewTypeEnum.List)}
  >
    <svg
      xmlns="http://www.w3.org/2000/svg"
      class="h-5 w-5 mr-1"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        stroke-linecap="round"
        stroke-linejoin="round"
        stroke-width="2"
        d="M4 6h16M4 10h16M4 14h16M4 18h16"
      />
    </svg>
    List
  </button>
</div>
