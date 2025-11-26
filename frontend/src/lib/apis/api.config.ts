import {
  type ConfigurationParameters,
  GitApi,
  GitHubApi,
  KnowledgeApi,
  LLMsApi,
  LLMKeysApi,
  MissionsApi,
  ToolsApi,
  AuthApi,
  AuthenticationApi,
  UsersApi,
} from "holly-api";
import { Configuration, ConversationsApi } from "holly-api";
import { derived, get } from "svelte/store";
import { accessToken, isAuthenticated } from "$lib/store/auth/tokens.store";
import { tokenRefreshMiddleware } from "$lib/apis/middleware";

export const cfPagesCommitSha = import.meta.env.VITE_CF_PAGES_COMMIT_SHA;
export const cfPagesBranch = import.meta.env.VITE_CF_PAGES_BRANCH;
export const schema = import.meta.env.VITE_SCHEMA;
export let serverName = import.meta.env.VITE_SERVER;
const port = import.meta.env.VITE_PORT;
if (port != "") {
  serverName = `${serverName}:${port}`;
}

export const baseURL = `${schema}://${serverName}`;

// Create reactive headers that update when accessToken changes
export const headers = derived(accessToken, (token) => {
  return {
    Authorization: token ? `Bearer ${token}` : "",
  };
});

// Create reactive configuration that updates when headers change
const reactiveConfig = derived(headers, (currentHeaders) => {
  const configParams: ConfigurationParameters = {
    basePath: baseURL,
    credentials: "include",
    headers: currentHeaders,
    middleware: [tokenRefreshMiddleware], // Add token refresh middleware
  };
  return new Configuration(configParams);
});

// Create derived stores for all API clients that automatically update when config changes
export const authApi = derived(reactiveConfig, (config) => new AuthApi(config));

export const authenticationApi = derived(
  reactiveConfig,
  (config) => new AuthenticationApi(config),
);

export const conversationApi = derived(
  reactiveConfig,
  (config) => new ConversationsApi(config),
);

export const gitApi = derived(reactiveConfig, (config) => new GitApi(config));

export const githubApi = derived(
  reactiveConfig,
  (config) => new GitHubApi(config),
);

export const toolsApi = derived(
  reactiveConfig,
  (config) => new ToolsApi(config),
);

export const llmsApi = derived(reactiveConfig, (config) => new LLMsApi(config));

export const knowledgeApi = derived(
  reactiveConfig,
  (config) => new KnowledgeApi(config),
);

export const missionApi = derived(
  reactiveConfig,
  (config) => new MissionsApi(config),
);

export const llmKeysApi = derived(
  reactiveConfig,
  (config) => new LLMKeysApi(config),
);

export const usersApi = derived(
  reactiveConfig,
  (config) => new UsersApi(config),
);

// Export function to set access token
export function setAccessToken(token: string | null) {
  if (token === null || token === undefined || token === "") {
    accessToken.set("");
    isAuthenticated.set(false);
  } else {
    accessToken.set(token);
    isAuthenticated.set(true);
  }
}

// Export function to clear access token
export function clearAccessToken() {
  accessToken.set("");
}

// Export function to get current access token
export function getAccessToken(): string | null {
  return get(accessToken);
}
