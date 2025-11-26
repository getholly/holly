import { usersApi } from "$lib/apis/api.config";
import { get } from "svelte/store";
import { browser } from "$app/environment";
import { withTokenRefresh } from "$lib/apis/auth/token-manager";
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
  return withTokenRefresh(async () => {
    const gitHubOAuthInitiateRequest: GitHubOAuthInitiateRequest = {
      redirect_url: redirectUrl,
      scopes: scopes,
    };

    return await getUsersApiClient().hollyUsersApiRouterInitiateGithubOauth({
      gitHubOAuthInitiateRequest,
    });
  });
}

export async function handleGitHubOAuthCallback(
  code: string,
  state: string,
): Promise<GitHubOAuthCallbackResponse> {
  return withTokenRefresh(async () => {
    const gitHubOAuthCallbackRequest: GitHubOAuthCallbackRequest = {
      code,
      state,
    };

    return await getUsersApiClient().hollyUsersApiRouterHandleGithubOauthCallback(
      {
        gitHubOAuthCallbackRequest,
      },
    );
  });
}

export async function getGitHubConnectionStatus(): Promise<ConnectionStatusResponse> {
  return withTokenRefresh(async () => {
    return await getUsersApiClient().hollyUsersApiRouterGetGithubConnectionStatus();
  });
}

export async function listGitHubAccounts(): Promise<GitHubAccountListResponse> {
  return withTokenRefresh(async () => {
    return await getUsersApiClient().hollyUsersApiRouterListGithubAccounts();
  });
}

export async function disconnectGitHubAccount(
  githubLogin: string,
): Promise<GitHubAccountActionResponse> {
  return withTokenRefresh(async () => {
    const gitHubAccountActionRequest: GitHubAccountActionRequest = {
      github_login: githubLogin,
    };

    return await getUsersApiClient().hollyUsersApiRouterDisconnectGithubAccount(
      {
        gitHubAccountActionRequest,
      },
    );
  });
}

export async function setPrimaryGitHubAccount(
  githubLogin: string,
): Promise<GitHubAccountActionResponse> {
  return withTokenRefresh(async () => {
    const gitHubAccountActionRequest: GitHubAccountActionRequest = {
      github_login: githubLogin,
    };

    return await getUsersApiClient().hollyUsersApiRouterSetPrimaryGithubAccount(
      {
        gitHubAccountActionRequest,
      },
    );
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
