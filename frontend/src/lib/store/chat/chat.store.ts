import { get, writable } from "svelte/store";
import { persistableStore } from "$lib/store/persistable.store";
import type { Conversation, Message } from "holly-api";
import { getChatHistory } from "$lib/apis/conversation/api.conversation";

export const settings = writable({ audio: false });
export const prompt = writable("");

export const showChatModal = writable(false);

export const showAskModal = writable(false);

export const currentChatContractId = persistableStore(
  "currentChatContractId",
  0,
);

export const chatWithTools = persistableStore("chatWithTools", false);

export const chatTitle = persistableStore("chatTitle", "Conversation");

export const currentChatConversationId = persistableStore(
  "currentChatConversationId",
  "",
);

export const conversations = writable<Conversation[]>([]);

export const messages = writable<Message[]>([]);
export async function updateChatHistory() {
  const history = await getChatHistory(get(currentChatConversationId));
  messages.set(history?.messages || []);
}
