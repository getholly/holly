import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { getGitHubConnectionStatus } from "$lib/apis/users/github-oauth";

// Mock the API config
vi.mock("$lib/apis/api.config", () => ({
  usersApi: { subscribe: vi.fn() },
}));

// Mock svelte/store
vi.mock("svelte/store", () => ({
  get: vi.fn(),
}));

describe("GitHub OAuth API", () => {
  const mockGet = vi.mocked(get);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("getGitHubConnectionStatus", () => {
    it("calls the users API client directly (refresh handled by middleware)", async () => {
      const apiMethod = vi.fn().mockResolvedValue({
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
      });
      mockGet.mockReturnValue({
        hollyUsersApiRouterGetGithubConnectionStatus: apiMethod,
      });

      const result = await getGitHubConnectionStatus();

      expect(apiMethod).toHaveBeenCalledTimes(1);
      expect(result.is_connected).toBe(true);
      expect(result.total_accounts).toBe(1);
      expect(result.primary_account?.github_login).toBe("testuser");
    });

    it("propagates errors from the API client (e.g. after a failed refresh)", async () => {
      const apiMethod = vi.fn().mockRejectedValue({
        status: 401,
        message: "Unauthorized",
      });
      mockGet.mockReturnValue({
        hollyUsersApiRouterGetGithubConnectionStatus: apiMethod,
      });

      await expect(getGitHubConnectionStatus()).rejects.toMatchObject({
        status: 401,
        message: "Unauthorized",
      });
      expect(apiMethod).toHaveBeenCalledTimes(1);
    });
  });
});
