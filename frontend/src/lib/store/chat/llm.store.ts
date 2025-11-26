import { persistableStore } from "$lib/store/persistable.store";

// Store for the selected LLM in the chat context
export const selectedChatLlmId = persistableStore("selectedChatLlmId", "");
