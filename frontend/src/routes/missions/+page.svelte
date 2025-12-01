<script lang="ts">
  import { onMount } from "svelte";
  import { base } from "$app/paths";
  import {
    Modal,
    Button,
    Label,
    Input,
    Textarea,
    Badge,
    Spinner,
  } from "flowbite-svelte";
  import {
    PlusOutline,
    PenOutline,
    TrashBinOutline,
    PlayOutline,
    StopOutline,
    EyeOutline,
    ArrowLeftOutline,
  } from "flowbite-svelte-icons";
  import {
    getMissions,
    getMission,
    // createMission, // unused - mission creation via /wizard
    updateMission,
    deleteMission,
    startMissionSse,
    endMission,
  } from "$lib/apis/mission/api.mission";
  import type {
    MissionSummary,
    MissionDetail,
    // MissionCreate, // unused - mission creation via /wizard
    MissionUpdate,
  } from "holly-api";
  import { currentMission } from "$lib/store/mission/mission.store";

  // State
  let missions: MissionSummary[] = [];
  let isLoading = true;
  let error = "";
  let success = "";

  // Modal states
  // let showCreateModal = false; // unused - mission creation via /wizard
  let showEditModal = false;
  let showDeleteModal = false;
  let showDetailModal = false;

  // Selected mission for operations
  let selectedMission: MissionSummary | null = null;
  let missionDetail: MissionDetail | null = null;
  let isLoadingDetail = false;

  // Form data
  // createForm unused - mission creation via /wizard
  // let createForm: MissionCreate = {
  //   title: "",
  //   description: "",
  //   branch_name: "main",
  // };

  let editForm: MissionUpdate = {
    title: "",
    description: "",
    branch_name: "",
  };

  // Mission start/stop state
  let startingMissionId: string | null = null;
  let stoppingMissionId: string | null = null;
  let startProgress: string[] = [];

  onMount(async () => {
    await loadMissions();
  });

  async function loadMissions() {
    isLoading = true;
    error = "";
    try {
      missions = await getMissions();
    } catch (err) {
      error = "Failed to load missions. Please try again.";
      console.error("Error loading missions:", err);
    } finally {
      isLoading = false;
    }
  }

  // CREATE - unused, mission creation via /wizard
  // function openCreateModal() {
  //   createForm = { title: "", description: "", branch_name: "main" };
  //   error = "";
  //   success = "";
  //   showCreateModal = true;
  // }

  // async function handleCreate() {
  //   if (!createForm.title?.trim()) {
  //     error = "Title is required";
  //     return;
  //   }
  //   try {
  //     await createMission(createForm);
  //     showCreateModal = false;
  //     success = "Mission created successfully";
  //     await loadMissions();
  //     setTimeout(() => (success = ""), 3000);
  //   } catch (err) {
  //     error = "Failed to create mission. Please try again.";
  //     console.error("Error creating mission:", err);
  //   }
  // }

  // READ (View Details)
  async function openDetailModal(mission: MissionSummary) {
    selectedMission = mission;
    missionDetail = null;
    isLoadingDetail = true;
    showDetailModal = true;
    try {
      missionDetail = await getMission(mission.id);
    } catch (err) {
      error = "Failed to load mission details.";
      console.error("Error loading mission details:", err);
    } finally {
      isLoadingDetail = false;
    }
  }

  // UPDATE
  function openEditModal(mission: MissionSummary) {
    selectedMission = mission;
    editForm = {
      title: mission.title,
      description: "",
      branch_name: mission.branch_name,
    };
    error = "";
    success = "";
    showEditModal = true;
    // Fetch full details for description
    getMission(mission.id).then((detail) => {
      editForm.description = detail.description || "";
    });
  }

  async function handleUpdate() {
    if (!selectedMission) return;
    if (!editForm.title?.trim()) {
      error = "Title is required";
      return;
    }
    try {
      await updateMission(selectedMission.id, editForm);
      showEditModal = false;
      success = "Mission updated successfully";
      await loadMissions();
      setTimeout(() => (success = ""), 3000);
    } catch (err) {
      error = "Failed to update mission. Please try again.";
      console.error("Error updating mission:", err);
    }
  }

  // DELETE
  function openDeleteModal(mission: MissionSummary) {
    selectedMission = mission;
    error = "";
    showDeleteModal = true;
  }

  async function handleDelete() {
    if (!selectedMission) return;
    try {
      await deleteMission(selectedMission.id);
      showDeleteModal = false;
      success = "Mission deleted successfully";
      // Clear current mission if it was the deleted one
      if ($currentMission?.id === selectedMission.id) {
        currentMission.set(null);
      }
      await loadMissions();
      setTimeout(() => (success = ""), 3000);
    } catch (err) {
      error = "Failed to delete mission. Please try again.";
      console.error("Error deleting mission:", err);
    }
  }

  // START Mission
  async function handleStartMission(mission: MissionSummary) {
    startingMissionId = mission.id;
    startProgress = [];
    error = "";
    try {
      await startMissionSse(mission.id, (data) => {
        if (data.message) {
          startProgress = [...startProgress, data.message];
        }
      });
      success = "Mission started successfully";
      await loadMissions();
      setTimeout(() => (success = ""), 3000);
    } catch (err) {
      error = "Failed to start mission.";
      console.error("Error starting mission:", err);
    } finally {
      startingMissionId = null;
      startProgress = [];
    }
  }

  // STOP Mission
  async function handleStopMission(mission: MissionSummary) {
    stoppingMissionId = mission.id;
    error = "";
    try {
      await endMission(mission.id, { state: "completed" });
      success = "Mission stopped successfully";
      await loadMissions();
      setTimeout(() => (success = ""), 3000);
    } catch (err) {
      error = "Failed to stop mission.";
      console.error("Error stopping mission:", err);
    } finally {
      stoppingMissionId = null;
    }
  }

  // Select mission and go to chat
  function selectAndChat(mission: MissionSummary) {
    getMission(mission.id).then((detail) => {
      currentMission.set(detail);
      window.location.href = `${base}/sse-chat`;
    });
  }

  // Handle edit from detail modal
  function handleEditFromDetail() {
    showDetailModal = false;
    if (selectedMission) {
      openEditModal(selectedMission);
    }
  }

  // Badge color based on state
  function getStateBadgeColor(
    state: string,
  ): "green" | "yellow" | "red" | "blue" | "dark" {
    switch (state.toLowerCase()) {
      case "active":
        return "green";
      case "pending":
      case "draft":
        return "yellow";
      case "completed":
        return "blue";
      case "aborted":
      case "failed":
        return "red";
      default:
        return "dark";
    }
  }

  function formatDate(date: Date): string {
    return new Date(date).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  }
</script>

<svelte:head>
  <title>Mission Control</title>
  <meta name="description" content="Manage your Holly missions" />
  <meta name="robots" content="noindex" />
</svelte:head>

<div class="min-h-screen bg-gray-50 dark:bg-gradient-to-br dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 transition-colors duration-300">
  <!-- Header -->
  <header class="border-b border-gray-200 dark:border-slate-700/50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-sm sticky top-0 z-40 transition-colors duration-300">
    <div class="max-w-7xl mx-auto px-6 py-4">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-4">
          <a
            href="{base}/dashboard"
            class="flex items-center gap-2 text-gray-500 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <ArrowLeftOutline class="w-4 h-4" />
            <span class="text-sm">Dashboard</span>
          </a>
          <div class="h-6 w-px bg-gray-300 dark:bg-slate-700"></div>
          <h1 class="text-2xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 dark:from-cyan-400 dark:to-blue-500 bg-clip-text text-transparent">
            Mission Control
          </h1>
        </div>
        <a
          href="{base}/wizard"
          class="inline-flex items-center px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-lg border-0 shadow-lg shadow-cyan-500/25 transition-all"
        >
          <PlusOutline class="w-4 h-4 mr-2" />
          New Mission
        </a>
      </div>
    </div>
  </header>

  <!-- Main Content -->
  <main class="max-w-7xl mx-auto px-6 py-8">
    <!-- Alerts -->
    {#if error}
      <div class="mb-6 p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400" role="alert">
        <span class="font-medium">Error:</span> {error}
      </div>
    {/if}
    {#if success}
      <div class="mb-6 p-4 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-700 dark:bg-emerald-500/10 dark:border-emerald-500/30 dark:text-emerald-400" role="alert">
        <span class="font-medium">Success:</span> {success}
      </div>
    {/if}

    <!-- Start Progress -->
    {#if startingMissionId && startProgress.length > 0}
      <div class="mb-6 p-4 rounded-lg bg-cyan-50 border border-cyan-200 dark:bg-cyan-500/10 dark:border-cyan-500/30">
        <div class="flex items-center gap-3 mb-3">
          <Spinner size="4" color="blue" />
          <span class="text-cyan-700 dark:text-cyan-400 font-medium">Starting mission...</span>
        </div>
        <div class="space-y-1 text-sm text-gray-600 dark:text-slate-400 font-mono">
          {#each startProgress as msg}
            <div class="flex items-center gap-2">
              <span class="text-cyan-600 dark:text-cyan-500">▸</span>
              {msg}
            </div>
          {/each}
        </div>
      </div>
    {/if}

    <!-- Loading State -->
    {#if isLoading}
      <div class="flex flex-col items-center justify-center py-24">
        <div class="relative">
          <div class="w-16 h-16 border-4 border-gray-200 dark:border-slate-700 rounded-full"></div>
          <div class="absolute top-0 left-0 w-16 h-16 border-4 border-cyan-500 rounded-full animate-spin border-t-transparent"></div>
        </div>
        <p class="mt-6 text-gray-500 dark:text-slate-400">Loading missions...</p>
      </div>

    <!-- Empty State -->
    {:else if missions.length === 0}
      <div class="flex flex-col items-center justify-center py-24 text-center">
        <div class="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500/20 to-blue-500/20 flex items-center justify-center mb-6">
          <svg class="w-12 h-12 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">No missions yet</h2>
        <p class="text-gray-500 dark:text-slate-400 mb-8 max-w-md">
          Missions help you organize your work with Holly. Create your first mission to get started.
        </p>
        <a
          href="{base}/wizard"
          class="inline-flex items-center px-6 py-3 text-base font-medium text-white bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-lg border-0 shadow-lg shadow-cyan-500/25 transition-all"
        >
          <PlusOutline class="w-5 h-5 mr-2" />
          Create Your First Mission
        </a>
      </div>

    <!-- Mission Grid -->
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {#each missions as mission (mission.id)}
          <div
            class="group relative bg-white dark:bg-slate-800/50 backdrop-blur-sm border border-gray-200 dark:border-slate-700/50 rounded-xl overflow-hidden hover:border-cyan-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-cyan-500/10"
          >
            <!-- Card Header -->
            <div class="p-5 pb-4">
              <div class="flex items-start justify-between mb-3">
                <h3 class="text-lg font-semibold text-gray-900 dark:text-white truncate pr-2 group-hover:text-cyan-600 dark:group-hover:text-cyan-400 transition-colors">
                  {mission.title}
                </h3>
                <Badge color={getStateBadgeColor(mission.state)} class="shrink-0">
                  {mission.state}
                </Badge>
              </div>

              <!-- Meta Info -->
              <div class="space-y-2 text-sm text-gray-500 dark:text-slate-400">
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-gray-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span class="truncate">{mission.owner}</span>
                </div>
                <div class="flex items-center gap-2">
                  <svg class="w-4 h-4 text-gray-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  <span class="font-mono text-xs bg-gray-100 dark:bg-slate-700/50 px-2 py-0.5 rounded">{mission.branch_name}</span>
                </div>
                <div class="flex items-center gap-4">
                  <div class="flex items-center gap-1.5">
                    <svg class="w-4 h-4 text-gray-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                    </svg>
                    <span>{mission.repository_count} repos</span>
                  </div>
                  <div class="flex items-center gap-1.5">
                    <svg class="w-4 h-4 text-gray-400 dark:text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                    <span>{formatDate(mission.updated_at)}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Card Actions -->
            <div class="px-5 py-3 bg-gray-50 dark:bg-slate-900/50 border-t border-gray-200 dark:border-slate-700/50 flex items-center justify-between">
              <div class="flex items-center gap-1">
                <button
                  class="p-2 rounded-lg text-gray-400 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-slate-700/50 transition-colors"
                  title="View Details"
                  on:click={() => openDetailModal(mission)}
                >
                  <EyeOutline class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded-lg text-gray-400 dark:text-slate-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-200 dark:hover:bg-slate-700/50 transition-colors"
                  title="Edit Mission"
                  on:click={() => openEditModal(mission)}
                >
                  <PenOutline class="w-4 h-4" />
                </button>
                <button
                  class="p-2 rounded-lg text-gray-400 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                  title="Delete Mission"
                  on:click={() => openDeleteModal(mission)}
                >
                  <TrashBinOutline class="w-4 h-4" />
                </button>
              </div>

              <div class="flex items-center gap-2">
                {#if mission.state === "active"}
                  <button
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-amber-700 dark:text-amber-400 bg-amber-50 dark:bg-amber-500/10 hover:bg-amber-100 dark:hover:bg-amber-500/20 transition-colors disabled:opacity-50"
                    disabled={stoppingMissionId === mission.id}
                    on:click={() => handleStopMission(mission)}
                  >
                    {#if stoppingMissionId === mission.id}
                      <Spinner size="3" />
                    {:else}
                      <StopOutline class="w-3.5 h-3.5" />
                    {/if}
                    Stop
                  </button>
                {:else}
                  <button
                    class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-500/10 hover:bg-emerald-100 dark:hover:bg-emerald-500/20 transition-colors disabled:opacity-50"
                    disabled={startingMissionId === mission.id}
                    on:click={() => handleStartMission(mission)}
                  >
                    {#if startingMissionId === mission.id}
                      <Spinner size="3" />
                    {:else}
                      <PlayOutline class="w-3.5 h-3.5" />
                    {/if}
                    Start
                  </button>
                {/if}
                <button
                  class="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium text-cyan-700 dark:text-cyan-400 bg-cyan-50 dark:bg-cyan-500/10 hover:bg-cyan-100 dark:hover:bg-cyan-500/20 transition-colors"
                  on:click={() => selectAndChat(mission)}
                >
                  Chat
                  <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14 5l7 7m0 0l-7 7m7-7H3" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </main>
</div>

<!-- Create Mission Modal (unused - mission creation happens via /wizard) -->
<!--
<Modal bind:open={showCreateModal} size="md" title="Create New Mission" autoclose={false} class="dark">
  <form on:submit|preventDefault={handleCreate} class="space-y-5">
    <div>
      <Label for="create-title" class="mb-2 text-gray-700 dark:text-slate-300">Title *</Label>
      <Input
        id="create-title"
        bind:value={createForm.title}
        placeholder="Enter mission title"
        required
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div>
      <Label for="create-description" class="mb-2 text-gray-700 dark:text-slate-300">Description</Label>
      <Textarea
        id="create-description"
        bind:value={createForm.description}
        placeholder="Describe your mission objectives..."
        rows={4}
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div>
      <Label for="create-branch" class="mb-2 text-gray-700 dark:text-slate-300">Branch Name</Label>
      <Input
        id="create-branch"
        bind:value={createForm.branch_name}
        placeholder="main"
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-slate-700">
      <Button color="alternative" on:click={() => (showCreateModal = false)}>Cancel</Button>
      <Button type="submit" color="blue" class="bg-gradient-to-r from-cyan-500 to-blue-600 border-0">
        Create Mission
      </Button>
    </div>
  </form>
</Modal>
-->

<!-- Edit Mission Modal -->
<Modal bind:open={showEditModal} size="md" title="Edit Mission" autoclose={false}>
  <form on:submit|preventDefault={handleUpdate} class="space-y-5">
    <div>
      <Label for="edit-title" class="mb-2 text-gray-700 dark:text-slate-300">Title *</Label>
      <Input
        id="edit-title"
        bind:value={editForm.title}
        placeholder="Enter mission title"
        required
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div>
      <Label for="edit-description" class="mb-2 text-gray-700 dark:text-slate-300">Description</Label>
      <Textarea
        id="edit-description"
        bind:value={editForm.description}
        placeholder="Describe your mission objectives..."
        rows={4}
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div>
      <Label for="edit-branch" class="mb-2 text-gray-700 dark:text-slate-300">Branch Name</Label>
      <Input
        id="edit-branch"
        bind:value={editForm.branch_name}
        placeholder="main"
        class="bg-gray-50 dark:bg-slate-800 border-gray-300 dark:border-slate-600 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-slate-400 focus:border-cyan-500 focus:ring-cyan-500"
      />
    </div>
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-slate-700">
      <Button color="alternative" on:click={() => (showEditModal = false)}>Cancel</Button>
      <Button type="submit" color="blue" class="bg-gradient-to-r from-cyan-500 to-blue-600 border-0">
        Save Changes
      </Button>
    </div>
  </form>
</Modal>

<!-- Delete Confirmation Modal -->
<Modal bind:open={showDeleteModal} size="sm" title="Delete Mission" autoclose={false}>
  <div class="space-y-4">
    <p class="text-gray-700 dark:text-slate-300">
      Are you sure you want to delete this mission? This action cannot be undone.
    </p>
    {#if selectedMission}
      <div class="p-4 rounded-lg bg-red-50 border border-red-200 text-red-700 dark:bg-red-500/10 dark:border-red-500/30 dark:text-red-400">
        <p class="text-sm">
          <strong>Mission:</strong> {selectedMission.title}
        </p>
      </div>
    {/if}
    <div class="flex justify-end gap-3 pt-4 border-t border-gray-200 dark:border-slate-700">
      <Button color="alternative" on:click={() => (showDeleteModal = false)}>Cancel</Button>
      <Button color="red" on:click={handleDelete}>
        <TrashBinOutline class="w-4 h-4 mr-2" />
        Delete Mission
      </Button>
    </div>
  </div>
</Modal>

<!-- Mission Detail Modal -->
<Modal bind:open={showDetailModal} size="lg" title="Mission Details" autoclose={false}>
  {#if isLoadingDetail}
    <div class="flex items-center justify-center py-12">
      <Spinner size="8" color="blue" />
    </div>
  {:else if missionDetail}
    <div class="space-y-6">
      <!-- Header -->
      <div class="flex items-start justify-between">
        <div>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">{missionDetail.title}</h2>
          <p class="text-gray-500 dark:text-slate-400 mt-1">{missionDetail.description || "No description"}</p>
        </div>
        <Badge color={getStateBadgeColor(missionDetail.state)} class="text-sm">
          {missionDetail.state}
        </Badge>
      </div>

      <!-- Info Grid -->
      <div class="grid grid-cols-2 gap-4">
        <div class="p-4 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700/50">
          <div class="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">Branch</div>
          <div class="font-mono text-sm text-cyan-600 dark:text-cyan-400">{missionDetail.branch_name}</div>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700/50">
          <div class="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">Owner</div>
          <div class="text-sm text-gray-900 dark:text-white">{missionDetail.owner?.email || "Unknown"}</div>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700/50">
          <div class="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">Container</div>
          <div class="text-sm">
            {#if missionDetail.container_id}
              <span class="text-emerald-600 dark:text-emerald-400">Running</span>
            {:else}
              <span class="text-gray-400 dark:text-slate-400">Not started</span>
            {/if}
          </div>
        </div>
        <div class="p-4 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700/50">
          <div class="text-xs text-gray-500 dark:text-slate-500 uppercase tracking-wider mb-1">Updated</div>
          <div class="text-sm text-gray-900 dark:text-white">{formatDate(missionDetail.updated_at)}</div>
        </div>
      </div>

      <!-- Repositories -->
      <div>
        <h3 class="text-sm font-medium text-gray-700 dark:text-slate-300 mb-3">Repositories ({missionDetail.repositories?.length || 0})</h3>
        {#if missionDetail.repositories && missionDetail.repositories.length > 0}
          <div class="space-y-2">
            {#each missionDetail.repositories as repo}
              <div class="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-slate-800/50 border border-gray-200 dark:border-slate-700/50">
                <div class="flex items-center gap-3">
                  <svg class="w-5 h-5 text-gray-400 dark:text-slate-500" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 .5C5.73.5.77 5.46.77 11.74c0 4.93 3.2 9.11 7.64 10.59.56.1.77-.24.77-.54v-2.1c-3.11.68-3.77-1.31-3.77-1.31-.51-1.29-1.25-1.63-1.25-1.63-1.02-.7.08-.68.08-.68 1.13.08 1.73 1.16 1.73 1.16 1 .1 2.07.76 2.47 1.16.1-.74.39-1.25.71-1.54-2.51-.29-5.15-1.25-5.15-5.56 0-1.23.44-2.23 1.16-3.02-.12-.28-.5-1.43.11-2.98 0 0 .95-.3 3.12 1.16.9-.25 1.86-.38 2.82-.38.96 0 1.92.13 2.82.38 2.17-1.46 3.12-1.16 3.12-1.16.61 1.55.23 2.7.12 2.98.72.79 1.16 1.79 1.16 3.02 0 4.33-2.65 5.26-5.18 5.55.4.34.77 1.02.77 2.06v3.06c0 .31.2.65.78.54 4.42-1.48 7.62-5.66 7.62-10.59C23.23 5.46 18.27.5 12 .5z" />
                  </svg>
                  <div>
                    <div class="text-sm font-medium text-gray-900 dark:text-white">{repo.name}</div>
                    <div class="text-xs text-gray-500 dark:text-slate-500">{repo.owner}</div>
                  </div>
                </div>
              </div>
            {/each}
          </div>
        {:else}
          <p class="text-sm text-gray-500 dark:text-slate-500">No repositories connected</p>
        {/if}
      </div>

      <!-- Collaborators -->
      {#if missionDetail.collaborators && missionDetail.collaborators.length > 0}
        <div>
          <h3 class="text-sm font-medium text-gray-700 dark:text-slate-300 mb-3">Collaborators ({missionDetail.collaborators.length})</h3>
          <div class="flex flex-wrap gap-2">
            {#each missionDetail.collaborators as collab}
              <span class="px-3 py-1 rounded-full bg-gray-100 dark:bg-slate-700/50 text-sm text-gray-700 dark:text-slate-300">
                {collab.email}
              </span>
            {/each}
          </div>
        </div>
      {/if}
    </div>

    <div class="flex justify-end gap-3 pt-6 mt-6 border-t border-gray-200 dark:border-slate-700">
      <Button color="alternative" on:click={() => (showDetailModal = false)}>Close</Button>
      <Button color="blue" class="bg-gradient-to-r from-cyan-500 to-blue-600 border-0" on:click={handleEditFromDetail}>
        <PenOutline class="w-4 h-4 mr-2" />
        Edit Mission
      </Button>
    </div>
  {/if}
</Modal>
