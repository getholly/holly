<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import { writable } from "svelte/store";

  export let missionId: string;

  interface CloneStatus {
    status: string;
    message?: string;
    current_repo?: number;
    total_repos?: number;
    repo_name?: string;
    error?: string;
    cloned_repos?: string[];
    failed_repos?: Array<{ repo: string; error: string }>;
    timestamp?: number;
  }

  const cloneStatus = writable<CloneStatus | null>(null);
  const isConnected = writable(false);
  const errorMessage = writable<string | null>(null);

  let eventSource: EventSource | null = null;

  onMount(() => {
    connectToSSE();
  });

  onDestroy(() => {
    disconnectSSE();
  });

  function connectToSSE() {
    const url = `/api/holly/missions/${missionId}/clone-status/stream`;

    try {
      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        $isConnected = true;
        $errorMessage = null;
      };

      eventSource.onmessage = (event) => {
        try {
          const data: CloneStatus = JSON.parse(event.data);
          $cloneStatus = data;

          // Close connection if clone is completed or failed
          if (data.status === "completed" || data.status === "failed") {
            setTimeout(() => disconnectSSE(), 1000);
          }
        } catch (err) {
          console.error("Failed to parse SSE data:", err);
        }
      };

      eventSource.onerror = (err) => {
        console.error("SSE error:", err);
        $isConnected = false;
        $errorMessage = "Connection lost. Retrying...";

        // Retry connection after 5 seconds
        setTimeout(() => {
          if (!$isConnected) {
            connectToSSE();
          }
        }, 5000);
      };
    } catch (err) {
      console.error("Failed to connect to SSE:", err);
      $errorMessage = "Failed to connect to clone status stream";
    }
  }

  function disconnectSSE() {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
      $isConnected = false;
    }
  }

  function getProgressPercentage(): number {
    if (!$cloneStatus || !$cloneStatus.total_repos) return 0;
    return Math.round(
      (($cloneStatus.current_repo || 0) / $cloneStatus.total_repos) * 100,
    );
  }

  function getStatusColor(): string {
    if (!$cloneStatus) return "gray";
    switch ($cloneStatus.status) {
      case "started":
      case "cloning":
      case "progress":
        return "blue";
      case "completed":
        return "green";
      case "failed":
        return "red";
      default:
        return "gray";
    }
  }
</script>

<div class="clone-status-monitor p-4 border rounded-lg shadow-sm">
  <h3 class="text-lg font-semibold mb-3">Repository Clone Status</h3>

  {#if $errorMessage}
    <div class="alert alert-error mb-3">
      <span>{$errorMessage}</span>
    </div>
  {/if}

  {#if $cloneStatus}
    <div class="status-info space-y-2">
      <!-- Status Badge -->
      <div class="flex items-center gap-2">
        <span class="text-sm font-medium">Status:</span>
        <span class="badge badge-{getStatusColor()}">
          {$cloneStatus.status}
        </span>
      </div>

      <!-- Message -->
      {#if $cloneStatus.message}
        <p class="text-sm text-gray-600">{$cloneStatus.message}</p>
      {/if}

      <!-- Progress Bar -->
      {#if $cloneStatus.total_repos && $cloneStatus.status === "progress"}
        <div class="progress-section">
          <div class="flex justify-between text-sm mb-1">
            <span>Progress</span>
            <span
              >{$cloneStatus.current_repo || 0} / {$cloneStatus.total_repos}</span
            >
          </div>
          <div class="w-full bg-gray-200 rounded-full h-2.5">
            <div
              class="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style="width: {getProgressPercentage()}%"
            ></div>
          </div>
          {#if $cloneStatus.repo_name}
            <p class="text-xs text-gray-500 mt-1">
              Currently cloning: {$cloneStatus.repo_name}
            </p>
          {/if}
        </div>
      {/if}

      <!-- Completed Repos -->
      {#if $cloneStatus.cloned_repos && $cloneStatus.cloned_repos.length > 0}
        <div class="completed-section">
          <h4 class="text-sm font-medium mb-1">Successfully Cloned:</h4>
          <ul class="list-disc list-inside text-sm text-gray-600">
            {#each $cloneStatus.cloned_repos as repo}
              <li>{repo}</li>
            {/each}
          </ul>
        </div>
      {/if}

      <!-- Failed Repos -->
      {#if $cloneStatus.failed_repos && $cloneStatus.failed_repos.length > 0}
        <div class="failed-section">
          <h4 class="text-sm font-medium text-red-600 mb-1">
            Failed Repositories:
          </h4>
          <ul class="space-y-1">
            {#each $cloneStatus.failed_repos as failure}
              <li class="text-sm">
                <span class="text-red-600">{failure.repo}:</span>
                <span class="text-gray-600">{failure.error}</span>
              </li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  {:else if $isConnected}
    <p class="text-sm text-gray-500">Waiting for clone status updates...</p>
  {:else}
    <p class="text-sm text-gray-500">Connecting to status stream...</p>
  {/if}

  <!-- Connection Status -->
  <div class="mt-3 flex items-center gap-2">
    <div
      class="w-2 h-2 rounded-full {$isConnected
        ? 'bg-green-500'
        : 'bg-red-500'}"
    ></div>
    <span class="text-xs text-gray-500">
      {$isConnected ? "Connected" : "Disconnected"}
    </span>
  </div>
</div>

<style>
  .clone-status-monitor {
    background-color: #f9fafb;
    max-width: 600px;
  }

  .badge {
    @apply px-2 py-1 text-xs rounded-full font-medium;
  }

  .badge-blue {
    @apply bg-blue-100 text-blue-800;
  }

  .badge-green {
    @apply bg-green-100 text-green-800;
  }

  .badge-red {
    @apply bg-red-100 text-red-800;
  }

  .badge-gray {
    @apply bg-gray-100 text-gray-800;
  }

  .alert {
    @apply p-3 rounded-md;
  }

  .alert-error {
    @apply bg-red-50 text-red-800;
  }
</style>
