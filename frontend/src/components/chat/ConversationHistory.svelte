<script lang="ts">
  import { Listgroup, ListgroupItem } from "flowbite-svelte";
  import { TrashBinOutline } from "flowbite-svelte-icons";
  import { formatDateYYYYMMDD } from "$lib/utils/dateUtils";
  import type { Conversation, ConversationSummary } from "holly-api";
  import {
    conversations,
    currentChatConversationId,
    updateChatHistory,
  } from "$lib/store/chat/chat.store";
  import { onMount } from "svelte";
  import { getConversations } from "$lib/apis/conversation/api.conversation";
  import DeleteChatModal from "$components/chat/DeleteChatModal.svelte";
  import { currentMission } from "$lib/store/mission/mission.store";

  let showDeleteModal = false;
  let conversation: Conversation | undefined = undefined;
  let groupedConversations = new Map();

  // React to changes in the currentMission store
  $: {
    if ($currentMission && $currentMission.conversations) {
      // Convert MissionConversationSchema[] to ConversationSummary[]
      const missionConversations = $currentMission.conversations.map(
        (conv) => ({
          id: conv.conversation_id,
          title: conv.title || conv.conversation_id,
          created_at: conv.created_at,
          // Add other necessary fields
          updated_at: conv.updated_at,
        }),
      );
      conversations.set(missionConversations);
      groupConversationsByDate();
    } else {
      conversations.set([]);
      groupConversationsByDate();
    }
  }

  onMount(async () => {
    // Only fetch from API if we don't already have conversations from currentMission
    if (!$currentMission || !$currentMission.conversations) {
      conversations.set(await getConversations());
    }
    groupConversationsByDate();
  });

  // Format date as "8th April 2025"
  function formatDateWithOrdinal(date) {
    const dateObj = new Date(date);
    const day = dateObj.getDate();
    const month = dateObj.toLocaleString("en-US", { month: "long" });
    const year = dateObj.getFullYear();

    // Add ordinal suffix to day
    const ordinalSuffix = getOrdinalSuffix(day);

    return `${day}${ordinalSuffix} ${month} ${year}`;
  }

  // Get ordinal suffix for day (st, nd, rd, th)
  function getOrdinalSuffix(day) {
    if (day > 3 && day < 21) return "th";
    switch (day % 10) {
      case 1:
        return "st";
      case 2:
        return "nd";
      case 3:
        return "rd";
      default:
        return "th";
    }
  }

  // Group conversations by their exact date
  function groupConversationsByDate() {
    groupedConversations = new Map();

    // Sort conversations by date (newest first)
    const sortedConversations = [...$conversations].sort((a, b) => {
      if (!a.created_at || !b.created_at) return 0;
      return (
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    });

    sortedConversations.forEach((conv) => {
      if (conv.created_at) {
        const dateObj = new Date(conv.created_at);
        // We'll use the ISO date as the key for sorting/grouping
        const isoDate = dateObj.toISOString().split("T")[0];
        // But display the formatted date
        const formattedDate = formatDateWithOrdinal(dateObj);

        if (!groupedConversations.has(isoDate)) {
          // Store both the ISO date (as key) and formatted date (for display)
          groupedConversations.set(isoDate, {
            displayDate: formattedDate,
            conversations: [],
          });
        }

        groupedConversations.get(isoDate).conversations.push(conv);
      }
    });
  }

  // Watch for changes in the conversations store
  $: {
    if ($conversations) {
      groupConversationsByDate();
    }
  }

  async function selectConversation(conversation: Conversation) {
    currentChatConversationId.set(conversation.id || "");
    await updateChatHistory();
  }

  function enableDeleteModal(conv: Conversation) {
    showDeleteModal = true;
    conversation = conv;
  }
</script>

<h2 class="text-xl font-bold mb-4 dark:text-gray-200">
  Previous Conversations
</h2>
<div class="h-full">
  <Listgroup class="h-full cursor-pointer border-0 bg-transparent divide-y-0">
    {#each Array.from(groupedConversations.entries()) as [isoDate, group]}
      <div class="mb-4">
        <div class="font-semibold text-sm mb-2">{group.displayDate}</div>
        <Listgroup class="border-0 bg-transparent divide-y-0">
          {#each group.conversations as conv}
            <ListgroupItem
              class="bg-transparent py-1 border-0 bg-white py-2 my-2 text-left"
            >
              <div class="flex justify-between items-center">
                <div class="flex-grow">
                  <button
                    on:click={() => selectConversation(conv)}
                    class="hover:underline"
                  >
                    {conv.title || conv.id}
                  </button>
                </div>
                <button
                  on:click={() => enableDeleteModal(conv)}
                  class="text-gray-500 hover:text-gray-700"
                >
                  <TrashBinOutline />
                </button>
              </div>
            </ListgroupItem>
          {/each}
        </Listgroup>
      </div>
    {:else}
      <div class="text-gray-500 dark:text-gray-400 text-center my-4">
        No previous conversations found for this mission.
      </div>
    {/each}
  </Listgroup>
</div>

<DeleteChatModal {showDeleteModal} conversationToDelete={conversation} />
