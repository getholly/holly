import type { LLMsApi, LLMSchema } from "holly-api";
import { llmsApi } from "$lib/apis/api.config";
import { get } from "svelte/store";

// Initialize the LLMs API with the same configuration pattern used for other APIs
function getApiClient(): LLMsApi {
  return get(llmsApi);
}

/**
 * TypeScript interface for creating a new LLM
 */
export interface LLMCreateData {
  name: string;
  full_name: string;
  base_url?: string | null;
  system_prompt?: string | null;
  top_p?: number | null;
  top_k?: number | null;
  min_p?: number | null;
  temperature?: number | null;
  max_tokens?: number | null;
}

/**
 * TypeScript interface for updating an LLM
 */
export interface LLMUpdateData {
  name?: string | null;
  full_name?: string | null;
  base_url?: string | null;
  system_prompt?: string | null;
  top_p?: number | null;
  top_k?: number | null;
  min_p?: number | null;
  temperature?: number | null;
  max_tokens?: number | null;
}

/**
 * Get a list of all available LLMs (system + user's custom LLMs)
 * @returns Promise<Array<LLMSchema>> A list of available LLM models
 */
export async function getLLMs(): Promise<Array<LLMSchema>> {
  try {
    return await getApiClient().hollyHollyApiViewsLlmListLlms();
  } catch (error) {
    console.error("Error fetching LLMs:", error);
    throw error;
  }
}

/**
 * Get a specific LLM by ID
 * @param id The ID of the LLM to retrieve
 * @returns Promise<LLMSchema> The requested LLM
 */
export async function getLLM(id: number): Promise<LLMSchema> {
  try {
    return await getApiClient().hollyHollyApiViewsLlmGetLlm({ llmId: id });
  } catch (error) {
    console.error(`Error fetching LLM with ID ${id}:`, error);
    throw error;
  }
}

/**
 * Create a new custom LLM
 * @param data The LLM configuration data
 * @returns Promise<LLMSchema> The created LLM
 */
export async function createLLM(data: LLMCreateData): Promise<LLMSchema> {
  try {
    return await getApiClient().hollyHollyApiViewsLlmCreateLlm({
      requestBody: data as any,
    });
  } catch (error) {
    console.error("Error creating LLM:", error);
    throw error;
  }
}

/**
 * Update an existing custom LLM
 * @param id The ID of the LLM to update
 * @param data The updated LLM configuration data
 * @returns Promise<LLMSchema> The updated LLM
 */
export async function updateLLM(
  id: number,
  data: LLMUpdateData,
): Promise<LLMSchema> {
  try {
    return await getApiClient().hollyHollyApiViewsLlmUpdateLlm({
      llmId: id,
      requestBody: data as any,
    });
  } catch (error) {
    console.error(`Error updating LLM with ID ${id}:`, error);
    throw error;
  }
}

/**
 * Delete a custom LLM
 * @param id The ID of the LLM to delete
 * @returns Promise<void>
 */
export async function deleteLLM(id: number): Promise<void> {
  try {
    await getApiClient().hollyHollyApiViewsLlmDeleteLlm({ llmId: id });
  } catch (error) {
    console.error(`Error deleting LLM with ID ${id}:`, error);
    throw error;
  }
}
