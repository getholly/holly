<script lang="ts">
  import NewMessageButton from "$components/chat/NewMessageButton.svelte";
  import NewChatModal from "$components/chat/NewChatModal.svelte";

  import {
    currentChatConversationId,
    chatTitle,
    messages,
    updateChatHistory,
  } from "$lib/store/chat/chat.store";
  import { refreshConversations } from "$lib/apis/conversation/api.conversation";
  import MsgLog from "$components/chat/MsgLog.svelte";
  import { createEventDispatcher } from "svelte";
  import { createMissionConversation } from "$lib/apis/mission/api.mission";
  import { currentMission } from "$lib/store/mission/mission.store";
  import { selectedChatLlmId } from "$lib/store/chat/llm.store";
  import LlmSelector from "$components/settings/LlmSelector.svelte";
  import RepoBranchSelectorModal from "$components/gitrepo/RepoBranchSelectorModal.svelte";
  import {
    primaryRepoFullName,
    primaryBranchName,
  } from "$lib/store/chat/repo.store";

  const dispatch = createEventDispatcher();

  let showNewChatModal = false;
  let showRepoModal = false;

  function handleNewChat() {
    // Show the modal instead of dispatching directly
    showNewChatModal = true;
  }

  function handleModalClose() {
    showNewChatModal = false;
  }

  async function handleModalSubmit(title: string, initialMessage: string) {
    try {
      // Create a new chat conversation with the given title and initial message

      if (!$currentMission) {
        console.error("No current mission found.");
        return;
      }

      const conversationData = {
        title,
        initial_message: initialMessage,
      };

      const newConversation = await createMissionConversation(
        $currentMission.id,
        conversationData,
      );
      // Update the current conversation ID in the store
      if (newConversation.success === true && newConversation.conversation_id) {
        currentChatConversationId.set(newConversation.conversation_id);
      } else {
        console.error(
          `Failed to create new conversation: ${newConversation.message}`,
        );
        return;
      }

      // Update the conversation title in the store
      $chatTitle = title;

      // Refresh the conversations list
      await refreshConversations();

      // Update the messages in the store
      await updateChatHistory();

      // Dispatch event for any parent components that need to know
      dispatch("newMessage");
    } catch (error) {
      console.error("Failed to create new conversation:", error);
    }
  }

  function handleLlmSelected(event) {
    const { id, name } = event.detail;
    console.log(`LLM selected in header: ${name} (ID: ${id})`);
  }

  export let childMsgLog: MsgLog | null = null;
  export let conversationTitle = "Chat";
</script>

<div class="flex flex-col md:flex-row items-center justify-between px-4 h-full">
  <div class="text-base p-2 dark:text-gray-200">
    {conversationTitle}:{$currentChatConversationId}
    <br />
    <!--        <span class="text-sm text-green-600">Streaming Enabled</span>-->
  </div>

  <div class="flex gap-4">
    <div class="flex gap-4 justify-center items-center">
      <LlmSelector
        bind:selectedLlmId={$selectedChatLlmId}
        on:llmSelected={handleLlmSelected}
      />
      <button
        class="text-xs md:text-sm flex gap-2 items-center dark:bg-gray-800 px-2 py-2 rounded-2xl dark:text-gray-400 opacity-80 dark:opacity-100 hover:opacity-100 dark:hover:text-gray-300 duration-300"
        on:click={() => (showRepoModal = true)}
      >
        <img
          alt="github icon"
          class="w-4 h-4 dark:invert-[.75]"
          height="8"
          src="img/github-logo.png"
        />{$primaryRepoFullName || "Repo"}
      </button>
      <button
        class="text-xs md:text-sm flex gap-2 items-center dark:bg-gray-800 px-2 py-2 rounded-2xl dark:text-gray-400 opacity-80 dark:opacity-100 hover:opacity-100 dark:hover:text-gray-300 duration-300"
        on:click={() => (showRepoModal = true)}
      >
        <img
          alt="branch icon"
          class="w-3 h-4 dark:invert-[.75]"
          height="8"
          src="img/branch-icon.png"
        />{$primaryBranchName || "Branch"}
      </button>
    </div>
    <NewMessageButton bind:msgLog={childMsgLog} />
    <button
      id="new-chat-button"
      class=" focus:ring-0 flex gap-2 bg-theme-primary-dark py-2 px-4 rounded-lg flex justify-center items-center"
      on:click={handleNewChat}
    >
      <img
        src="img/plus-icon.png"
        width="14"
        height="14"
        alt="chat icon"
        class="w-3 h-3"
      />
    </button>
  </div>
</div>

<!-- Add the NewChatModal component -->
<NewChatModal
  bind:display={showNewChatModal}
  onClose={handleModalClose}
  onSubmit={(title, message) => handleModalSubmit(title, message)}
/>

<RepoBranchSelectorModal
  open={showRepoModal}
  on:close={() => (showRepoModal = false)}
/>
