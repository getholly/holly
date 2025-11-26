import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { getGitHubConnectionStatus } from "$lib/apis/users/github-oauth";
import { usersApi } from "$lib/apis/api.config";
import { withTokenRefresh } from "$lib/apis/auth/token-manager";

// Mock the API config
vi.mock("$lib/apis/api.config", () => ({
  usersApi: { subscribe: vi.fn() },
}));

// Mock the token manager
vi.mock("$lib/apis/auth/token-manager", () => ({
  withTokenRefresh: vi.fn(),
}));

// Mock svelte/store
vi.mock("svelte/store", () => ({
  get: vi.fn(),
}));

describe("GitHub OAuth API", () => {
  const mockGet = vi.mocked(get);
  const mockWithTokenRefresh = vi.mocked(withTokenRefresh);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getGitHubConnectionStatus", () => {
    it("should call API with token refresh wrapper", async () => {
      // Setup
      const mockApiClient = {
        githubmeUsersApiRouterGetGithubConnectionStatus: vi
          .fn()
          .mockResolvedValue({
            is_connected: true,
            total_accounts: 1,
            primary_account: {
              github_login: "testuser",
              github_id: 12345,
              avatar_url: "https://avatar.url",
              is_primary: true,
              is_active: true,
              created_at: "2023-01-01T00:00:00Z",
            },
          }),
      };

      mockGet.mockReturnValue(mockApiClient);

      // Mock withTokenRefresh to execute the API call directly
      mockWithTokenRefresh.mockImplementation(async (apiCall) => {
        return await apiCall();
      });

      // Execute
      const result = await getGitHubConnectionStatus();

      // Assert
      expect(mockWithTokenRefresh).toHaveBeenCalledTimes(1);
      expect(result.is_connected).toBe(true);
      expect(result.total_accounts).toBe(1);
      expect(result.primary_account?.github_login).toBe("testuser");
    });

    it("should handle 401 errors through token refresh mechanism", async () => {
      // Setup
      const mockApiClient = {
        githubmeUsersApiRouterGetGithubConnectionStatus: vi
          .fn()
          .mockRejectedValue({
            status: 401,
            message: "Unauthorized",
          }),
      };

      mockGet.mockReturnValue(mockApiClient);

      // Mock withTokenRefresh to propagate the error (simulating failed token refresh)
      mockWithTokenRefresh.mockRejectedValue({
        status: 401,
        message: "Unauthorized",
      });

      // Execute & Assert
      await expect(getGitHubConnectionStatus()).rejects.toMatchObject({
        status: 401,
        message: "Unauthorized",
      });

      expect(mockWithTokenRefresh).toHaveBeenCalledTimes(1);
    });

    it("should handle successful token refresh and retry", async () => {
      // Setup
      const mockApiClient = {
        githubmeUsersApiRouterGetGithubConnectionStatus: vi
          .fn()
          .mockResolvedValue({
            is_connected: false,
            total_accounts: 0,
            primary_account: null,
          }),
      };

      mockGet.mockReturnValue(mockApiClient);

      // Mock withTokenRefresh to simulate successful retry after token refresh
      mockWithTokenRefresh.mockImplementation(async (apiCall) => {
        // Simulate the token manager successfully refreshing and retrying
        return await apiCall();
      });

      // Execute
      const result = await getGitHubConnectionStatus();

      // Assert
      expect(mockWithTokenRefresh).toHaveBeenCalledTimes(1);
      expect(result.is_connected).toBe(false);
      expect(result.total_accounts).toBe(0);
      expect(result.primary_account).toBeNull();
    });
  });
});
