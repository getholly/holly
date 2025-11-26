import { describe, it, expect, vi, beforeEach } from "vitest";
import { get } from "svelte/store";
import { tokenManager, withTokenRefresh } from "$lib/apis/auth/token-manager";
import {
  accessToken,
  refreshToken,
  isAuthenticated,
  logout,
} from "$lib/store/auth/tokens.store";
import { refreshTokenAndUpdateConfig } from "$lib/apis/auth/api.auth";

// Mock the auth API
vi.mock("$lib/apis/auth/api.auth", () => ({
  refreshTokenAndUpdateConfig: vi.fn(),
}));

// Mock the stores
vi.mock("$lib/store/auth/tokens.store", () => ({
  accessToken: { subscribe: vi.fn(), set: vi.fn() },
  refreshToken: { subscribe: vi.fn(), set: vi.fn() },
  isAuthenticated: { subscribe: vi.fn(), set: vi.fn() },
  logout: vi.fn(),
}));

// Mock svelte/store
vi.mock("svelte/store", () => ({
  get: vi.fn(),
}));

describe("Token Manager", () => {
  const mockGet = vi.mocked(get);
  const mockRefreshTokenAndUpdateConfig = vi.mocked(
    refreshTokenAndUpdateConfig,
  );
  const mockLogout = vi.mocked(logout);

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("withTokenRefresh", () => {
    it("should execute API call successfully when user is authenticated", async () => {
      // Setup
      mockGet
        .mockReturnValueOnce(true) // isAuthenticated
        .mockReturnValueOnce("valid-access-token"); // accessToken

      const mockApiCall = vi.fn().mockResolvedValue({ success: true });

      // Execute
      const result = await withTokenRefresh(mockApiCall);

      // Assert
      expect(result).toEqual({ success: true });
      expect(mockApiCall).toHaveBeenCalledTimes(1);
    });

    it("should throw error when user is not authenticated", async () => {
      // Setup
      mockGet
        .mockReturnValueOnce(false) // isAuthenticated
        .mockReturnValueOnce(""); // accessToken

      const mockApiCall = vi.fn();

      // Execute & Assert
      await expect(withTokenRefresh(mockApiCall)).rejects.toThrow(
        "User not authenticated",
      );
      expect(mockApiCall).not.toHaveBeenCalled();
    });

    it("should refresh token and retry on 401 error", async () => {
      // Setup
      mockGet
        .mockReturnValueOnce(true) // isAuthenticated (first call)
        .mockReturnValueOnce("expired-token") // accessToken (first call)
        .mockReturnValueOnce("valid-refresh-token") // refreshToken for refresh
        .mockReturnValueOnce(true) // isAuthenticated (retry call)
        .mockReturnValueOnce("new-access-token"); // accessToken (retry call)

      const authError = { status: 401, message: "Unauthorized" };
      const mockApiCall = vi
        .fn()
        .mockRejectedValueOnce(authError)
        .mockResolvedValueOnce({ success: true });

      mockRefreshTokenAndUpdateConfig.mockResolvedValueOnce({
        access: "new-access-token",
        refresh: "new-refresh-token",
      });

      // Execute
      const result = await withTokenRefresh(mockApiCall);

      // Assert
      expect(result).toEqual({ success: true });
      expect(mockApiCall).toHaveBeenCalledTimes(2);
      expect(mockRefreshTokenAndUpdateConfig).toHaveBeenCalledWith(
        "valid-refresh-token",
      );
    });

    it("should logout user when token refresh fails", async () => {
      // Setup
      mockGet
        .mockReturnValueOnce(true) // isAuthenticated
        .mockReturnValueOnce("expired-token") // accessToken
        .mockReturnValueOnce("invalid-refresh-token"); // refreshToken

      const authError = { status: 401, message: "Unauthorized" };
      const mockApiCall = vi.fn().mockRejectedValue(authError);

      mockRefreshTokenAndUpdateConfig.mockRejectedValue(
        new Error("Invalid refresh token"),
      );

      // Execute & Assert
      await expect(withTokenRefresh(mockApiCall)).rejects.toThrow(
        "Unauthorized",
      );
      expect(mockLogout).toHaveBeenCalled();
    });

    it("should not retry on non-auth errors", async () => {
      // Setup
      mockGet
        .mockReturnValueOnce(true) // isAuthenticated
        .mockReturnValueOnce("valid-token"); // accessToken

      const networkError = { status: 500, message: "Internal Server Error" };
      const mockApiCall = vi.fn().mockRejectedValue(networkError);

      // Execute & Assert
      await expect(withTokenRefresh(mockApiCall)).rejects.toThrow(
        "Internal Server Error",
      );
      expect(mockApiCall).toHaveBeenCalledTimes(1);
      expect(mockRefreshTokenAndUpdateConfig).not.toHaveBeenCalled();
    });

    it("should respect maxRetries parameter", async () => {
      // Setup
      mockGet
        .mockReturnValue(true) // isAuthenticated (multiple calls)
        .mockReturnValue("expired-token"); // accessToken (multiple calls)

      const authError = { status: 401, message: "Unauthorized" };
      const mockApiCall = vi.fn().mockRejectedValue(authError);

      // Mock multiple failed refresh attempts
      mockRefreshTokenAndUpdateConfig.mockRejectedValue(
        new Error("Refresh failed"),
      );

      // Execute & Assert
      await expect(withTokenRefresh(mockApiCall, 2)).rejects.toThrow(
        "Unauthorized",
      );
      expect(mockApiCall).toHaveBeenCalledTimes(3); // Initial + 2 retries
    });

    it("should handle concurrent token refresh requests", async () => {
      // Setup
      mockGet
        .mockReturnValue(true) // isAuthenticated
        .mockReturnValue("expired-token"); // accessToken

      const authError = { status: 401, message: "Unauthorized" };
      const mockApiCall1 = vi
        .fn()
        .mockRejectedValueOnce(authError)
        .mockResolvedValueOnce({ result: "call1" });
      const mockApiCall2 = vi
        .fn()
        .mockRejectedValueOnce(authError)
        .mockResolvedValueOnce({ result: "call2" });

      // Mock a slow refresh
      mockRefreshTokenAndUpdateConfig.mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  access: "new-token",
                  refresh: "new-refresh",
                }),
              100,
            ),
          ),
      );

      // Execute both calls concurrently
      const [result1, result2] = await Promise.all([
        withTokenRefresh(mockApiCall1),
        withTokenRefresh(mockApiCall2),
      ]);

      // Assert
      expect(result1).toEqual({ result: "call1" });
      expect(result2).toEqual({ result: "call2" });
      // Refresh should only be called once despite multiple concurrent requests
      expect(mockRefreshTokenAndUpdateConfig).toHaveBeenCalledTimes(1);
    });
  });
});
