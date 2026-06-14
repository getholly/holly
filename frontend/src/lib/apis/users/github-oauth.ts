import { usersApi } from "$lib/apis/api.config";
import { get } from "svelte/store";
import { browser } from "$app/environment";
// Token refresh is handled centrally by tokenRefreshMiddleware (wired into every
// API client in api.config.ts). Do not also wrap calls in withTokenRefresh — that
// caused two independent refresh mechanisms to race on a 401.
import type {
  UsersApi,
  GitHubOAuthInitiateRequest,
  GitHubOAuthInitiateResponse,
  GitHubOAuthCallbackRequest,
  GitHubOAuthCallbackResponse,
  GitHubAccountListResponse,
  GitHubAccountActionRequest,
  GitHubAccountActionResponse,
  ConnectionStatusResponse,
} from "holly-api";

function getUsersApiClient(): UsersApi {
  return get(usersApi);
}

export async function initiateGitHubOAuth(
  redirectUrl?: string,
  scopes?: string[],
): Promise<GitHubOAuthInitiateResponse> {
  const gitHubOAuthInitiateRequest: GitHubOAuthInitiateRequest = {
    redirect_url: redirectUrl,
    scopes: scopes,
  };

  return await getUsersApiClient().hollyUsersApiRouterInitiateGithubOauth({
    gitHubOAuthInitiateRequest,
  });
}

export async function handleGitHubOAuthCallback(
  code: string,
  state: string,
): Promise<GitHubOAuthCallbackResponse> {
  const gitHubOAuthCallbackRequest: GitHubOAuthCallbackRequest = {
    code,
    state,
  };

  return await getUsersApiClient().hollyUsersApiRouterHandleGithubOauthCallback({
    gitHubOAuthCallbackRequest,
  });
}

export async function getGitHubConnectionStatus(): Promise<ConnectionStatusResponse> {
  return await getUsersApiClient().hollyUsersApiRouterGetGithubConnectionStatus();
}

export async function listGitHubAccounts(): Promise<GitHubAccountListResponse> {
  return await getUsersApiClient().hollyUsersApiRouterListGithubAccounts();
}

export async function disconnectGitHubAccount(
  githubLogin: string,
): Promise<GitHubAccountActionResponse> {
  const gitHubAccountActionRequest: GitHubAccountActionRequest = {
    github_login: githubLogin,
  };

  return await getUsersApiClient().hollyUsersApiRouterDisconnectGithubAccount({
    gitHubAccountActionRequest,
  });
}

export async function setPrimaryGitHubAccount(
  githubLogin: string,
): Promise<GitHubAccountActionResponse> {
  const gitHubAccountActionRequest: GitHubAccountActionRequest = {
    github_login: githubLogin,
  };

  return await getUsersApiClient().hollyUsersApiRouterSetPrimaryGithubAccount({
    gitHubAccountActionRequest,
  });
}

export async function startGitHubOAuthFlow(
  redirectUrl?: string,
): Promise<void> {
  if (!browser) return;

  try {
    const response = await initiateGitHubOAuth(redirectUrl);

    // Redirect to GitHub OAuth URL
    window.location.href = response.oauth_url;
  } catch (error) {
    throw error;
  }
}
