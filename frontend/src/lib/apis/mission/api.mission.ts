import { missionApi, baseURL } from "$lib/apis/api.config";
import { get } from "svelte/store";
import {
  accessToken,
  refreshToken as refreshTokenStore,
} from "$lib/store/auth/tokens.store";
import { refreshTokenAndUpdateConfig } from "$lib/apis/auth/api.auth";
import type {
  MissionDetail,
  MissionSummary,
  GenericResponse,
  ContainerStartResponse,
  MissionCreate,
  MissionUpdate,
  MissionStateUpdate,
  MissionConversationCreate,
  MissionConversationUpdate,
  MissionCollaboratorSchema,
  MissionKnowledgeSchema,
  MissionKnowledgeSetSchema,
  MissionRepositoryAddSchema,
  MissionRepositoryRemoveSchema,
  MissionRepositorySetSchema,
  MissionToolSchema,
  MissionToolSetSchema,
  HollyHollyApiViewsMissionGetMissionRequest,
  HollyHollyApiViewsMissionCreateMissionRequest,
  HollyHollyApiViewsMissionUpdateMissionRequest,
  HollyHollyApiViewsMissionStartMissionRequest,
  HollyHollyApiViewsMissionEndMissionRequest,
  HollyHollyApiViewsMissionCreateConversationRequest,
  HollyHollyApiViewsMissionUpdateConversationSummaryRequest,
  HollyHollyApiViewsMissionAddRepositoriesRequest,
  HollyHollyApiViewsMissionRemoveRepositoriesRequest,
  HollyHollyApiViewsMissionSetRepositoriesRequest,
  HollyHollyApiViewsMissionAddCollaboratorsRequest,
  HollyHollyApiViewsMissionRemoveCollaboratorsRequest,
  HollyHollyApiViewsMissionAddKnowledgeItemsRequest,
  HollyHollyApiViewsMissionRemoveKnowledgeItemsRequest,
  HollyHollyApiViewsMissionSetKnowledgeItemsRequest,
  HollyHollyApiViewsMissionAddToolsRequest,
  HollyHollyApiViewsMissionRemoveToolsRequest,
  HollyHollyApiViewsMissionSetToolsRequest,
  ConversationStartResponse,
} from "holly-api";
import { MissionsApi } from "holly-api";

/**
 * Helper function to get the API client
 * @returns The mission API client
 */
function getApiClient(): MissionsApi {
  return get(missionApi);
}

/**
 * Get a list of all missions accessible by the current user
 * @returns Promise<Array<MissionSummary>> A list of mission summaries
 */
export async function getMissions(): Promise<Array<MissionSummary>> {
  try {
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionListMissions();
  } catch (error) {
    console.error("Error fetching missions:", error);
    throw error;
  }
}

/**
 * Get detailed information about a mission
 * @param missionId The UUID of the mission to retrieve
 * @returns Promise<MissionDetail> The mission details
 */
export async function getMission(missionId: string): Promise<MissionDetail> {
  try {
    const req: HollyHollyApiViewsMissionGetMissionRequest = {
      missionId: missionId,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionGetMission(req);
  } catch (error) {
    console.error(`Error fetching mission with ID ${missionId}:`, error);
    throw error;
  }
}

/**
 * Create a new mission
 * @param missionData The data for the new mission
 * @returns Promise<MissionDetail> The created mission details
 */
export async function createMission(
  missionData: MissionCreate,
): Promise<MissionDetail> {
  try {
    const req: HollyHollyApiViewsMissionCreateMissionRequest = {
      missionCreate: missionData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionCreateMission(req);
  } catch (error) {
    console.error("Error creating mission:", error);
    throw error;
  }
}

/**
 * Update an existing mission
 * @param missionId The UUID of the mission to update
 * @param missionData The updated mission data
 * @returns Promise<MissionDetail> The updated mission details
 */
export async function updateMission(
  missionId: string,
  missionData: MissionUpdate,
): Promise<MissionDetail> {
  try {
    const req: HollyHollyApiViewsMissionUpdateMissionRequest = {
      missionId: missionId,
      missionUpdate: missionData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionUpdateMission(req);
  } catch (error) {
    console.error(`Error updating mission with ID ${missionId}:`, error);
    throw error;
  }
}

/**
 * Start a mission by creating a container
 * @param missionId The UUID of the mission to start
 * @returns Promise<ContainerStartResponse> Response with container information
 */
export async function startMission(
  missionId: string,
): Promise<ContainerStartResponse> {
  try {
    const req: HollyHollyApiViewsMissionStartMissionRequest = {
      missionId: missionId,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionStartMission(req);
  } catch (error) {
    console.error(`Error starting mission with ID ${missionId}:`, error);
    throw error;
  }
}

export async function startMissionSse(
  missionId: string,
  onEvent: (data: any) => void,
): Promise<void> {
  // Get the access token from the store
  let token = get(accessToken);

  // If no token, reject immediately
  if (!token) {
    throw new Error("No access token available. Please log in.");
  }

  // Try to refresh the token if it might be expired
  // Since access tokens last 5 minutes, we'll always try to get a fresh one for SSE
  try {
    const refreshTokenValue = get(refreshTokenStore);

    if (refreshTokenValue) {
      console.log("🔄 Refreshing token for SSE connection...");
      const response = await refreshTokenAndUpdateConfig(refreshTokenValue);
      if (response.access) {
        token = response.access;
        console.log("✅ Successfully refreshed token for SSE connection");
      }
    } else {
      console.warn("⚠️ No refresh token available");
    }
  } catch (refreshError) {
    console.warn(
      "⚠️ Could not refresh token, using existing token:",
      refreshError,
    );
    // Continue with existing token
  }

  return new Promise((resolve, reject) => {
    // Append token as query parameter since EventSource can't send custom headers
    const url = `${baseURL}/_api/holly/missions/sse/start/${missionId}${token ? `?token=${encodeURIComponent(token)}` : ""}`;
    const es = new EventSource(url, { withCredentials: true });
    es.onmessage = (event) => {
      if (event.data.trim() === "[DONE]") {
        es.close();
        resolve();
        return;
      }
      try {
        const data = JSON.parse(event.data);
        // Check for errors in the SSE response
        if (data.error) {
          console.error("SSE Error:", data);
          es.close();
          reject(new Error(data.error));
          return;
        }
        onEvent(data);
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };
    es.onerror = (err) => {
      console.error("SSE Connection error:", err);
      es.close();
      reject(err);
    };
  });
}

/**
 * End a mission (mark as completed or aborted)
 * @param missionId The UUID of the mission to end
 * @param stateUpdate The state update data
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function endMission(
  missionId: string,
  stateUpdate: MissionStateUpdate,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionEndMissionRequest = {
      missionId: missionId,
      missionStateUpdate: stateUpdate,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionEndMission(req);
  } catch (error) {
    console.error(`Error ending mission with ID ${missionId}:`, error);
    throw error;
  }
}

/**
 * Create a new conversation for a mission
 * @param missionId The UUID of the mission
 * @param conversationData The conversation data
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function createMissionConversation(
  missionId: string,
  conversationData: MissionConversationCreate,
): Promise<ConversationStartResponse> {
  try {
    const req: HollyHollyApiViewsMissionCreateConversationRequest = {
      missionId: missionId,
      missionConversationCreate: conversationData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionCreateConversation(req);
  } catch (error) {
    console.error(
      `Error creating conversation for mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Update a mission conversation with a summary
 * @param missionId The UUID of the mission
 * @param conversationId The ID of the conversation
 * @param conversationData The updated conversation data
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function updateConversationSummary(
  missionId: string,
  conversationId: string,
  conversationData: MissionConversationUpdate,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionUpdateConversationSummaryRequest = {
      missionId: missionId,
      conversationId: conversationId,
      missionConversationUpdate: conversationData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionUpdateConversationSummary(req);
  } catch (error) {
    console.error(
      `Error updating conversation summary for mission ${missionId}, conversation ${conversationId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Add repositories to a mission
 * @param missionId The UUID of the mission
 * @param repositoryData The repository data containing repository IDs to add
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function addRepositories(
  missionId: string,
  repositoryData: MissionRepositoryAddSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionAddRepositoriesRequest = {
      missionId: missionId,
      missionRepositoryAddSchema: repositoryData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionAddRepositories(req);
  } catch (error) {
    console.error(
      `Error adding repositories to mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Remove repositories from a mission
 * @param missionId The UUID of the mission
 * @param repositoryData The repository data containing repository IDs to remove
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function removeRepositories(
  missionId: string,
  repositoryData: MissionRepositoryRemoveSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionRemoveRepositoriesRequest = {
      missionId: missionId,
      missionRepositoryRemoveSchema: repositoryData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionRemoveRepositories(req);
  } catch (error) {
    console.error(
      `Error removing repositories from mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Add collaborators to a mission
 * @param missionId The UUID of the mission
 * @param collaboratorData The collaborator data containing user IDs to add
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function addCollaborators(
  missionId: string,
  collaboratorData: MissionCollaboratorSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionAddCollaboratorsRequest = {
      missionId: missionId,
      missionCollaboratorSchema: collaboratorData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionAddCollaborators(req);
  } catch (error) {
    console.error(
      `Error adding collaborators to mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Remove collaborators from a mission
 * @param missionId The UUID of the mission
 * @param collaboratorData The collaborator data containing user IDs to remove
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function removeCollaborators(
  missionId: string,
  collaboratorData: MissionCollaboratorSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionRemoveCollaboratorsRequest = {
      missionId: missionId,
      missionCollaboratorSchema: collaboratorData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionRemoveCollaborators(req);
  } catch (error) {
    console.error(
      `Error removing collaborators from mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Add knowledge items to a mission
 * @param missionId The UUID of the mission
 * @param knowledgeData The knowledge data containing knowledge item IDs to add
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function addKnowledgeItems(
  missionId: string,
  knowledgeData: MissionKnowledgeSchema,
): Promise<GenericResponse> {
  try {
    const api = getApiClient();
    const req: HollyHollyApiViewsMissionAddKnowledgeItemsRequest = {
      missionId: missionId,
      missionKnowledgeSchema: knowledgeData,
    };
    const response = await api.hollyHollyApiViewsMissionAddKnowledgeItems(req);

    return response;
  } catch (error) {
    console.error(
      `Error adding knowledge items to mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Remove knowledge items from a mission
 * @param missionId The UUID of the mission
 * @param knowledgeData The knowledge data containing knowledge item IDs to remove
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function removeKnowledgeItems(
  missionId: string,
  knowledgeData: MissionKnowledgeSchema,
): Promise<GenericResponse> {
  try {
    const api = getApiClient();
    const req: HollyHollyApiViewsMissionRemoveKnowledgeItemsRequest = {
      missionId: missionId,
      missionKnowledgeSchema: knowledgeData,
    };
    const response =
      await api.hollyHollyApiViewsMissionRemoveKnowledgeItems(req);

    return response;
  } catch (error) {
    console.error(
      `Error removing knowledge items from mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Set repositories for a mission (replaces all existing repositories)
 * @param missionId The UUID of the mission
 * @param repositoryData The repository data containing complete list of repositories to set
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function setRepositories(
  missionId: string,
  repositoryData: MissionRepositorySetSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionSetRepositoriesRequest = {
      missionId: missionId,
      missionRepositorySetSchema: repositoryData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionSetRepositories(req);
  } catch (error) {
    console.error(
      `Error setting repositories for mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Set knowledge items for a mission (replaces all existing knowledge items)
 * @param missionId The UUID of the mission
 * @param knowledgeData The knowledge data containing complete list of knowledge item IDs to set
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function setKnowledgeItems(
  missionId: string,
  knowledgeData: MissionKnowledgeSetSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionSetKnowledgeItemsRequest = {
      missionId: missionId,
      missionKnowledgeSetSchema: knowledgeData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionSetKnowledgeItems(req);
  } catch (error) {
    console.error(
      `Error setting knowledge items for mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Set tools for a mission (replaces all existing tools)
 * @param missionId The UUID of the mission
 * @param toolData The tool data containing complete list of tool IDs to set
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function setTools(
  missionId: string,
  toolData: MissionToolSetSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionSetToolsRequest = {
      missionId: missionId,
      missionToolSetSchema: toolData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionSetTools(req);
  } catch (error) {
    console.error(
      `Error setting tools for mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Add tools to a mission
 * @param missionId The UUID of the mission
 * @param toolData The tool data containing tool IDs to add
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function addTools(
  missionId: string,
  toolData: MissionToolSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionAddToolsRequest = {
      missionId: missionId,
      missionToolSchema: toolData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionAddTools(req);
  } catch (error) {
    console.error(`Error adding tools to mission with ID ${missionId}:`, error);
    throw error;
  }
}

/**
 * Remove tools from a mission
 * @param missionId The UUID of the mission
 * @param toolData The tool data containing tool IDs to remove
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function removeTools(
  missionId: string,
  toolData: MissionToolSchema,
): Promise<GenericResponse> {
  try {
    const req: HollyHollyApiViewsMissionRemoveToolsRequest = {
      missionId: missionId,
      missionToolSchema: toolData,
    };
    const api = getApiClient();
    return await api.hollyHollyApiViewsMissionRemoveTools(req);
  } catch (error) {
    console.error(
      `Error removing tools from mission with ID ${missionId}:`,
      error,
    );
    throw error;
  }
}

/**
 * Delete a mission
 * @param missionId The UUID of the mission to delete
 * @returns Promise<GenericResponse> Response indicating success or failure
 */
export async function deleteMission(
  missionId: string,
): Promise<GenericResponse> {
  try {
    const baseAPIUrl = baseURL;
    const token = get(accessToken);
    const response = await fetch(
      `${baseAPIUrl}/_api/holly/missions/${missionId}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        credentials: "include",
      },
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(
        errorData.detail ||
          errorData.message ||
          `HTTP ${response.status}: ${response.statusText}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error(`Error deleting mission with ID ${missionId}:`, error);
    throw error;
  }
}
