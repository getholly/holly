import { writable } from "svelte/store";
import type { LLMSchema } from "holly-api";
import { getLLMs } from "$lib/apis/staticdata/api.llm";
import {
  listApiKeys,
  createApiKey,
  updateApiKey,
  deleteApiKey,
} from "$lib/apis/llmkeys/api.llmkeys";
import type {
  UserLLMApiKeySchema,
  UserLLMApiKeyCreateSchema,
  UserLLMApiKeyUpdateSchema,
} from "$lib/types/user_llm_api_key";

// Create a writable store with empty initial value
export const llmModels = writable<LLMSchema[]>([]);

// Function to load and refresh the LLMs
export async function loadLLMs(): Promise<void> {
  try {
    const models = await getLLMs();
    llmModels.set(models);
  } catch (error) {
    console.error("Failed to load LLMs:", error);
    // Set an empty array to avoid undefined errors
    llmModels.set([]);
  }
}

// Format LLMs for a dropdown selection
export function formatLLMsForDropdown(
  models: LLMSchema[],
): { value: string; name: string }[] {
  return models.map((model) => ({
    value: String(model.id), // Convert ID to string for value
    name: model.name,
  }));
}

// User API Keys Store
export const userApiKeysStore = writable<UserLLMApiKeySchema[]>([]);

export async function loadUserApiKeys(): Promise<void> {
  try {
    const keys = await listApiKeys();
    userApiKeysStore.set(keys);
  } catch (error) {
    console.error("Failed to load user API keys:", error);
    userApiKeysStore.set([]);
  }
}

export async function addUserApiKey(
  data: UserLLMApiKeyCreateSchema,
): Promise<UserLLMApiKeySchema | null> {
  try {
    const newKey = await createApiKey(data);
    userApiKeysStore.update((keys) => [...keys, newKey]);
    return newKey;
  } catch (error) {
    console.error("Failed to add user API key:", error);
    throw error; // Re-throw to allow components to handle it
  }
}

export async function updateUserApiKey(
  apiKeyId: number,
  data: UserLLMApiKeyUpdateSchema,
): Promise<UserLLMApiKeySchema | null> {
  try {
    const updatedKey = await updateApiKey(apiKeyId, data);
    userApiKeysStore.update((keys) =>
      keys.map((key) => (key.id === apiKeyId ? updatedKey : key)),
    );
    return updatedKey;
  } catch (error) {
    console.error("Failed to update user API key:", error);
    throw error; // Re-throw to allow components to handle it
  }
}

export async function removeUserApiKey(apiKeyId: number): Promise<void> {
  try {
    await deleteApiKey(apiKeyId);
    userApiKeysStore.update((keys) =>
      keys.filter((key) => key.id !== apiKeyId),
    );
  } catch (error) {
    console.error("Failed to delete user API key:", error);
    throw error; // Re-throw to allow components to handle it
  }
}
