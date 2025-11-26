import { knowledgeApi } from "$lib/apis/api.config";
import type { KnowledgeApi, KnowledgeSchema } from "holly-api";
import { get } from "svelte/store";

/**
 * Helper function to get the API client
 * @returns The mission API client
 */
function getApiClient(): KnowledgeApi {
  return get(knowledgeApi);
}

/**
 * Get a list of all available Knowledge items
 * @returns Promise<Array<KnowledgeSchema>> A list of available knowledge items
 */
export async function getKnowledge(): Promise<Array<KnowledgeSchema>> {
  return await getApiClient().hollyHollyApiViewsKnowledgeListKnowledge();
}
