<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import {
    Listgroup,
    ListgroupItem,
    Button,
    Input,
    Modal,
  } from "flowbite-svelte";
  import type { Conversation, Message } from "holly-api";
  import MsgLog from "$components/chat/MsgLog.svelte";
  import {
    currentChatConversationId,
    prompt,
    conversations as conversationsStore,
  } from "$lib/store/chat/chat.store";
  import Mic from "$components/chat/Mic.svelte";
  import { TrashBinOutline } from "flowbite-svelte-icons";

  import { showToast } from "$lib/store/toast/toast.store";
  import { formatDateYYYYMMDD } from "$lib/utils/dateUtils";
  import {
    getConversations,
    start_conversation,
    getChatHistory,
    sendMessage,
  } from "$lib/apis/conversation/api.conversation";
  import NewChatModal from "$components/chat/NewChatModal.svelte";
  import { get } from "svelte/store";

  let conversations: Conversation[] = [];
  let conversationId: string = "";

  export let conversationTitle: string = "";
  export let useTools = false;
  let messages: Message[] = [];
  let isChatLoading = false;
  let showDeleteModal = false;
  let conversationToDelete = null;
  let showNewChatModal = false;

  onMount(async () => {
    await startNewConversation(conversationTitle, "");
    conversations = await getConversations();
  });

  onDestroy(() => {
    $currentChatConversationId = "";
  });

  function openDeleteModal(conversation) {
    conversationToDelete = conversation;
    showDeleteModal = true;
  }

  // Temporary placeholder until backend endpoint is implemented
  async function deleteConversation(conversationId: string) {
    console.log(`TODO: Delete conversation with ID: ${conversationId}`);
    // In a real implementation, this would call an API endpoint
    // For now, we'll just update the local store
    showToast(
      "Delete functionality not fully implemented in the backend",
      "warning",
    );
    // Update the conversations store to remove the deleted conversation
    conversationsStore.set(
      get(conversationsStore).filter((c) => c.id !== conversationId),
    );
    return true;
  }

  async function deleteConv() {
    if (conversationToDelete) {
      console.log(
        `Deleting conversation: ${conversationToDelete.conversation_id}`,
      );
      await deleteConversation(conversationToDelete.conversation_id);
      conversations = conversations.filter(
        (c) => c.conversation_id !== conversationToDelete?.conversation_id,
      );
      showDeleteModal = false;
      conversationToDelete = null;
    }
  }

  async function startNewConversation(
    chatTitle: string = conversationTitle,
    message: string = "",
  ) {
    let conversation: Conversation = await start_conversation(
      chatTitle,
      message,
    );
    $currentChatConversationId = conversation.id;
    conversationTitle = chatTitle;
    // Refresh the conversations list
    conversations = await getConversations();
    return conversation;
  }

  async function clearHandler() {
    $prompt = "";
  }

  async function updateChatHistory() {
    const history = await getChatHistory(conversationId);
    messages = history?.messages || [];
  }

  async function selectConversation(conversation: Conversation) {
    conversationId = conversation.id;
    await updateChatHistory();
  }

  async function sendChatHandler() {
    if ($prompt.trim() === "") {
      console.info("Please enter a prompt for the LLM");
      return;
    }

    isChatLoading = true;
    try {
      const response = await sendMessage(conversationId, $prompt);
      console.log(`RESP: ${JSON.stringify(response)}`);
      if (response.response.content) {
        $prompt = "";
        await updateChatHistory();
      } else {
        console.error("Error sending chat message");
        showToast("Error sending chat message", "error");
      }
    } catch (error) {
      console.error("Error in sendChatHandler:", error);
      showToast("Error sending chat message", "error");
    } finally {
      isChatLoading = false;
    }
  }

  function handleKeyPress(event: KeyboardEvent) {
    if (event.key === "Enter") {
      sendChatHandler();
    }
  }

  async function handleNewChatSubmit(title: string, initialMessage: string) {
    const conversation = await startNewConversation(title, initialMessage);
    conversationId = conversation.id;
    await updateChatHistory();

    // If there's an initial message, send it
    if (initialMessage.trim() !== "") {
      $prompt = initialMessage;
      await sendChatHandler();
    }
  }

  $: console.log(`showchat modal: ${showNewChatModal}`);
</script>

<div class="flex h-screen dark:text-gray-200">
  <div class="w-1/3 border-r p-4">
    <h2 class="text-xl font-bold mb-4">Previous Conversations</h2>
    <div class="h-full overflow-y-auto">
      <Listgroup class="h-full cursor-pointer">
        {#each conversations as conversation, i (conversation.id)}
          <ListgroupItem>
            <div class="flex flex-cols-3 justify-between items-center">
              <button on:click={() => selectConversation(conversation)}>
                {formatDateYYYYMMDD(conversation.created_at)}
              </button>
              <div>
                <button on:click={() => selectConversation(conversation)}>
                  <span class="font-semibold w-8 text-right">{i + 1}.</span>
                  {conversation.title || conversation.id}
                </button>
              </div>
              <button on:click={() => openDeleteModal(conversation)}>
                <TrashBinOutline />
              </button>
            </div>
          </ListgroupItem>
        {/each}
      </Listgroup>
    </div>
  </div>
  <div class="w-2/3 p-4">
    <div class="flex flex-cols-3 items-center justify-between">
      <div></div>
      <h2 class="text-xl text-center p-2">
        {conversationTitle}
        <br />
      </h2>
      <Button
        class="bg-theme-secondary hover:bg-theme-secondary focus:ring-0"
        on:click={() => (showNewChatModal = true)}>New Chat</Button
      >
    </div>
    <div
      class="w-full flex flex-col flex-grow justify-between xl:max-h-[38.5vw] dark:bg-gray-600"
    >
      <MsgLog msgs={messages} {isChatLoading} />
      <div
        class="rounded-sm p-2 bottom-0 flex align-bottom flex-col bg-gray-100 dark:bg-gray-700"
      >
        {#if conversationId}
          <div class="flex w-full gap-4 align-bottom items-center">
            <div class="flex-grow">
              <textarea
                id="tutorInput"
                placeholder="Hello, how may I help you?"
                bind:value={$prompt}
                class="bg-white focus:ring-0 focus:outline-none focus:border-gray-500 dark:focus:border-gray-100"
                on:keypress={handleKeyPress}
              />
            </div>
            <div class="bg-light-grey p-1 rounded">
              <Mic on:sendChatMessage={sendChatHandler} />
            </div>
            <div>
              <Button
                class="bg-theme-primary hover:bg-theme-secondary focus-within:ring-0 duration-300 dark:text-gray-100 dark:bg-theme-primary dark:hover:bg-theme-primary dark:hover:text-gray-100 dark:focus-within:ring-theme-primary"
                on:click={sendChatHandler}
                >Send
              </Button>
            </div>
            <div>
              <Button
                class="bg-gray-100 text-grey-700 px-2 hover:text-black hover:bg-gray-100 dark:bg-gray-600 dark:text-gray-100 dark:hover:bg-gray-600"
                on:click={clearHandler}
              >
                <TrashBinOutline />
              </Button>
            </div>
          </div>
        {:else}
          <div class="text-center">
            <p class="text-red-500">
              Please select a chat conversation or click to start a new one
            </p>
          </div>
        {/if}
      </div>
    </div>
  </div>
  <Modal bind:open={showDeleteModal} size="xs" autoclose={false}>
    <div class="text-center">
      <h3 class="mb-5 text-lg font-normal text-gray-500 dark:text-gray-400">
        Are you sure you want to delete this conversation? ({conversationToDelete?.title ||
          conversationToDelete?.id})
      </h3>
      <div class="flex justify-center gap-4">
        <Button color="red" on:click={deleteConv}>Yes, I'm sure</Button>
        <Button color="alternative" on:click={() => (showDeleteModal = false)}>
          No, cancel
        </Button>
      </div>
    </div>
  </Modal>

  <NewChatModal
    bind:display={showNewChatModal}
    onClose={() => (showNewChatModal = false)}
    onSubmit={handleNewChatSubmit}
  />
</div>
