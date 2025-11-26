<script lang="ts">
  import type {
    HollyHollyApiViewsConversationsSendMessageSseRequest,
    Message,
    MessageCreate,
  } from "holly-api";
  import StreamingRequest from "$lib/apis/StreamingRequest";
  import MsgLog from "$components/chat/MsgLog.svelte";
  import {
    currentChatConversationId,
    messages,
    prompt,
  } from "$lib/store/chat/chat.store";
  import { selectedChatLlmId } from "$lib/store/chat/llm.store";

  import ChatHeader from "$components/chat/chat_panel/ChatHeader.svelte";
  import ChatFooter from "$components/chat/chat_panel/ChatFooter.svelte";
  import { Spinner } from "flowbite-svelte";
  import { onDestroy, onMount } from "svelte";
  import {
    getChatHistory,
    refreshConversations,
  } from "$lib/apis/conversation/api.conversation";
  import { createMissionConversation } from "$lib/apis/mission/api.mission";
  import { showToast } from "$lib/store/toast/toast.store";
  import { get } from "svelte/store";
  import { removeSurroundingChar } from "$lib/utils/stringUtils";
  import { baseURL, getAccessToken } from "$lib/apis/api.config";
  import { currentMission } from "$lib/store/mission/mission.store";
  import { getCSRFToken } from "$lib/utils/tokenUtils";

  let childMsgLog: MsgLog | null = null;
  let isChatLoading = false;
  let showInitialSpinner: boolean = false;
  let streamingMessage: string = "";
  let currentEventSource: EventSource | null = null;
  let firstEventReceived: boolean = false;
  let isStreaming = false;

  export let conversationTitle: string = "";

  onMount(async () => {
    // Get CSRF token on mount
    getCSRFToken();
    //await startNewConversation(conversationTitle, "")
    await refreshConversations();
  });

  onDestroy(() => {
    $currentChatConversationId = "";
    closeEventSource();
  });

  async function sendSSEMessage(message: string, llm_id: string) {
    try {
      // Ensure we have a conversation ID; if not, create one
      let conversationId = get(currentChatConversationId);
      if (!conversationId) {
        if (!$currentMission) {
          showToast("error", "No mission selected");
          return;
        }
        const conversationData = {
          title: conversationTitle || "Conversation",
          initial_message: message,
        };
        const newConversation = await createMissionConversation(
          $currentMission.id,
          conversationData,
        );
        if (!newConversation.success || !newConversation.conversation_id) {
          showToast(
            "error",
            newConversation.message || "Failed to create conversation",
          );
          return;
        }
        conversationId = newConversation.conversation_id;
        currentChatConversationId.set(conversationId);
      }

      // Show loading state
      isChatLoading = true;
      showInitialSpinner = true;

      // Use non-streaming endpoint that executes tools
      const url = `${baseURL}/_api/holly/conversations/${conversationId}/messages`;
      console.log(`Sending message to: ${url}`);

      const body = {
        name: conversationId,
        id: parseInt(llm_id),
        content: message,
      };

      // Add the user message immediately
      const userMessage: Message = {
        id: crypto.randomUUID(),
        conversation_id: conversationId,
        role: "user",
        content: message,
        created_at: new Date(),
      };
      messages.set([...get(messages), userMessage]);
      scrollToBottom();

      // Make non-streaming POST request
      const token = getAccessToken();
      const response = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          Authorization: token ? `Bearer ${token}` : "",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      console.log("Response:", data);

      // Add assistant message
      const assistantMessage: Message = {
        id: data.assistant_message_id || crypto.randomUUID(),
        conversation_id: conversationId,
        role: "assistant",
        content: data.response?.content || data.content || "No response",
        created_at: new Date(),
      };

      messages.set([...get(messages), assistantMessage]);
      isChatLoading = false;
      showInitialSpinner = false;
      scrollToBottom();

      // Refresh conversation history
      await updateChatHistory();
    } catch (error) {
      console.error("Error in conversation:", error);
      showToast("error", "Error sending message");
      isChatLoading = false;
      showInitialSpinner = false;
    }
  }

  async function clearHandler() {
    $prompt = "";
  }

  async function updateChatHistory() {
    const history = await getChatHistory($currentChatConversationId);
    messages.set(history?.messages || []);
    scrollToBottom();
  }

  function closeEventSource() {
    if (currentEventSource) {
      currentEventSource.close();
      currentEventSource = null;
    }
  }

  async function createConversationId(chatTitle: string, message: string) {
    const conversationData = {
      title: chatTitle || "New Chat",
      initial_message: message,
    };
    if (get(currentMission)) {
      let response = await createMissionConversation(
        get(currentMission).id,
        conversationData,
      );
      if (response.success === true && response.conversation_id) {
        $currentChatConversationId = response.conversation_id;
        conversationTitle = chatTitle || "New Chat";
      }
    }
  }

  function scrollToBottom() {
    if (childMsgLog) {
      childMsgLog.scrollToBottom();
    }
  }

  async function handleNewConversation(event: CustomEvent) {
    const newTitle = event.detail;
    conversationTitle = "";
    if (newTitle) {
      conversationTitle = newTitle;
    }
    await createConversationId(conversationTitle, $prompt.trim());
  }

  async function sendChatHandler() {
    if ($prompt.trim() === "") {
      console.info("Please enter a prompt for the LLM");
      return;
    }

    // check if we have currentChatConversationId defined if not then
    // make request to get a conversation id
    try {
      if (!$currentChatConversationId) {
        // Create a new conversation with the message
        await createConversationId("New Chat", "");
      }
      // Use existing conversation
      await sendSSEMessage($prompt, $selectedChatLlmId);
      $prompt = "";
    } catch (error) {
      console.error("Error in sendChatHandler:", error);
      showToast("Error sending chat message", "error");
      isChatLoading = false;
    }
  }
</script>

<!-- Main container with explicit viewport height calculation -->
<div class="h-[calc(100vh-8rem)] flex flex-col relative test" {...$$restProps}>
  <!-- Header - fixed height at top -->
  <div class="flex-shrink-0 border-b border-gray-200 dark:border-gray-600 py-4">
    <ChatHeader {childMsgLog} on:notify={handleNewConversation} />
  </div>

  <!-- Chat content area - calculated height with scroll -->
  <div class="flex-1 relative overflow-hidden">
    <!-- Messages area - scrollable with calculated height -->
    <div class="h-[calc(100vh-16rem)] overflow-y-auto pb-20">
      <MsgLog bind:this={childMsgLog} {isChatLoading} />

      <!-- Show initial spinner while connecting -->
      {#if showInitialSpinner}
        <div class="flex justify-center items-center p-4">
          <Spinner color="blue" class="w-8 h-8" />
          <span class="ml-2 text-gray-600 dark:text-gray-300">Thinking...</span>
        </div>
      {/if}

      <!-- Show streaming message if available -->
      {#if streamingMessage}
        <div class="flex justify-end p-4 pb-2">
          <div
            class="bg-gray-200 rounded-lg p-4 max-w-[80%] shadow-sm dark:bg-gray-800 dark:text-gray-200 wrap-anywhere"
          >
            <div class="flex items-start">
              <div class="flex-shrink-0 mr-3">
                <div
                  class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white"
                >
                  AI
                </div>
              </div>
              <div class="flex-1 text-black dark:text-white">
                <div
                  class="text-black dark:text-white streaming-text typewriter"
                  id="streaming-text-component"
                >
                  {streamingMessage}
                </div>
                <div class="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Streaming...
                </div>
              </div>
            </div>
          </div>
        </div>
      {/if}
    </div>
    <!-- Footer - sticky at bottom with fixed positioning -->
    <div
      class="absolute bottom-1 left-0 right-0 bg-transparent z-10 max-w-[1000px] mx-auto rounded-lg"
    >
      <div class="rounded-sm p-2">
        <div class="flex flex-row items-center gap-1">
          <!-- LLM Model Selector (now very compact) -->
          <!-- Chat Input and Controls (with more space) -->
          <div class="flex-grow">
            <ChatFooter
              {isChatLoading}
              on:sendChatMessage={sendChatHandler}
              on:clearChat={clearHandler}
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .typewriter {
    animation: typewriter 0.5s steps(1) infinite alternate;
  }

  @keyframes typewriter {
    0% {
      opacity: 0.3;
    }
    100% {
      opacity: 1;
    }
  }

  .streaming-text {
    white-space: pre-wrap;
    word-wrap: break-word;
  }

  /* Ensure smooth scrolling */
  .overflow-y-auto {
    scroll-behavior: smooth;
  }

  /* Viewport height calculations - responsive adjustments */
  @media (max-height: 600px) {
    .h-\[calc\(100vh-8rem\)\] {
      height: calc(100vh - 4rem);
    }
    .h-\[calc\(100vh-16rem\)\] {
      height: calc(100vh - 8rem);
    }
  }

  @media (max-height: 400px) {
    .h-\[calc\(100vh-8rem\)\] {
      height: calc(100vh - 2rem);
    }
    .h-\[calc\(100vh-16rem\)\] {
      height: calc(100vh - 6rem);
    }
  }
</style>
