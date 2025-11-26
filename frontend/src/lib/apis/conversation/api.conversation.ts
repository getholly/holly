import { baseURL, conversationApi } from "$lib/apis/api.config";

import type {
  Conversation,
  ConversationCreate,
  MessageCreate,
  HollyHollyApiViewsConversationsStartConversationRequest,
  HollyHollyApiViewsConversationsGetConversationRequest,
  HollyHollyApiViewsConversationsSendMessageRequest,
  HollyHollyApiViewsConversationsSendMessageSseRequest,
  HollyHollyApiViewsConversationsListConversationsRequest,
  ConversationSummary,
  ConversationsApi,
} from "holly-api";
import { conversations } from "$lib/store/chat/chat.store";
import { get } from "svelte/store";
import { currentMission } from "$lib/store/mission/mission.store";

function getApiClient(): ConversationsApi {
  return get(conversationApi);
}

export async function start_conversation(
  title: string,
  message: string,
): Promise<Conversation> {
  // eslint-disable-next-line no-useless-catch
  try {
    const conversationCreate: ConversationCreate = {
      initial_message: message,
      title: title,
    };
    const req: HollyHollyApiViewsConversationsStartConversationRequest = {
      conversationCreate: conversationCreate,
    };
    // TODO: correct and use the right API method
    // getApiClient().hollyHollyApiViewsConversationsStartConversationSse()
    return await getApiClient().hollyHollyApiViewsConversationsStartConversation(
      req,
    );
  } catch (error) {
    throw error;
  }
}

export async function getConversations(): Promise<ConversationSummary[]> {
  // eslint-disable-next-line no-useless-catch
  try {
    if (!get(currentMission) || !get(currentMission).id) {
      return [];
    }
    const req: HollyHollyApiViewsConversationsListConversationsRequest = {
      missionId: get(currentMission)?.id,
    };
    return await getApiClient().hollyHollyApiViewsConversationsListConversations(
      req,
    );
  } catch (error) {
    throw error;
  }
}

export async function getChatHistory(
  conversation_id: string,
): Promise<Conversation> {
  // eslint-disable-next-line no-useless-catch
  try {
    const req: HollyHollyApiViewsConversationsGetConversationRequest = {
      conversationId: conversation_id,
    };
    return await getApiClient().hollyHollyApiViewsConversationsGetConversation(
      req,
    );
  } catch (error) {
    throw error;
  }
}

export async function sendMessage(
  conversation_id: string,
  message: string,
): Promise<object> {
  // eslint-disable-next-line no-useless-catch
  try {
    const msg: MessageCreate = {
      content: message,
    };
    const req: HollyHollyApiViewsConversationsSendMessageRequest = {
      conversationId: conversation_id,
      messageCreate: msg,
    };
    return await getApiClient().hollyHollyApiViewsConversationsSendMessage(req);
  } catch (error) {
    throw error;
  }
}

export async function sendMessageSSE(conversation_id: string, message: string) {
  const msg: MessageCreate = {
    content: message,
    name: "", // not actually used in the backend
  };
  const req: HollyHollyApiViewsConversationsSendMessageSseRequest = {
    conversationId: conversation_id,
    messageCreate: msg,
  };
  // this will return an EventSource object
  return await getApiClient().hollyHollyApiViewsConversationsSendMessageSse(
    req,
  );
}

export async function startSSE(conversation_id: string) {
  const url = `${baseURL}/api/conversations/sse/start_conversation/${conversation_id}`;
  console.log(`connecting to: ${url}`);
  return new EventSource(url);
}

export async function refreshConversations() {
  conversations.set(await getConversations());
}
