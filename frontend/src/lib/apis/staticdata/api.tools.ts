import { toolsApi } from "$lib/apis/api.config";
import type { ToolsApi, ToolSchema } from "holly-api";
import { get } from "svelte/store";

// Initialize the LLMs API with the same configuration pattern used for other APIs
function getApiClient(): ToolsApi {
  return get(toolsApi);
}

/**
 * Get a list of all available LLMs
 * @returns Promise<Array<LLMSchema>> A list of available LLM models
 */
export async function getTools(): Promise<Array<ToolSchema>> {
  return await getApiClient().hollyHollyApiViewsToolsListTools();
}
