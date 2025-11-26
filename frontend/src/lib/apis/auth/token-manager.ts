import { get } from "svelte/store";
import {
  accessToken,
  refreshToken as refreshTokenStore,
  isAuthenticated,
  logout as logoutUser,
} from "$lib/store/auth/tokens.store";
import { refreshTokenAndUpdateConfig } from "./api.auth";

/**
 * Token refresh manager that handles automatic token refresh and API call retries
 */
class TokenManager {
  private isRefreshing = false;
  private refreshPromise: Promise<string> | null = null;
  private failedQueue: Array<{
    resolve: (token: string) => void;
    reject: (error: Error) => void;
  }> = [];

  /**
   * Refresh the access token using the refresh token
   * @returns Promise that resolves to the new access token
   */
  async refreshAccessToken(): Promise<string> {
    // If we're already refreshing, return the existing promise
    if (this.isRefreshing && this.refreshPromise) {
      return this.refreshPromise;
    }

    this.isRefreshing = true;

    this.refreshPromise = this.performTokenRefresh();

    try {
      const newToken = await this.refreshPromise;
      this.processQueue(newToken, null);
      return newToken;
    } catch (error) {
      this.processQueue(null, error as Error);
      throw error;
    } finally {
      this.isRefreshing = false;
      this.refreshPromise = null;
    }
  }

  private async performTokenRefresh(): Promise<string> {
    const currentRefreshToken = get(refreshTokenStore);

    if (!currentRefreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      const response = await refreshTokenAndUpdateConfig(currentRefreshToken);

      if (!response.access) {
        throw new Error("Invalid refresh token response");
      }

      return response.access;
    } catch (error) {
      // If refresh fails, log the user out
      console.error("❌ Token refresh failed, logging out user");
      logoutUser();
      throw new Error("Failed to refresh token - user logged out");
    }
  }

  private processQueue(token: string | null, error: Error | null) {
    this.failedQueue.forEach(({ resolve, reject }) => {
      if (error) {
        reject(error);
      } else if (token) {
        resolve(token);
      }
    });

    this.failedQueue = [];
  }

  /**
   * Add a request to the queue while token is being refreshed
   */
  private enqueueRequest(): Promise<string> {
    return new Promise((resolve, reject) => {
      this.failedQueue.push({ resolve, reject });
    });
  }

  /**
   * Check if an error is a 401 authentication error
   */
  private isAuthError(error: unknown): boolean {
    if (typeof error === "object" && error !== null) {
      // Check for ApiException with 401 status
      if ("status" in error && error.status === 401) {
        return true;
      }

      // Check for fetch Response with 401 status
      if ("response" in error && error.response && "status" in error.response) {
        return error.response.status === 401;
      }

      // Check for generic 401 error in message
      if ("message" in error && typeof error.message === "string") {
        return (
          error.message.includes("401") ||
          error.message.includes("Unauthorized")
        );
      }
    }

    return false;
  }

  /**
   * Execute an API call with automatic token refresh on 401 errors
   * @param apiCall Function that makes the API call
   * @param maxRetries Maximum number of retry attempts (default: 1)
   * @returns Promise that resolves to the API call result
   */
  async executeWithTokenRefresh<T>(
    apiCall: () => Promise<T>,
    maxRetries: number = 1,
  ): Promise<T> {
    let attempts = 0;

    while (attempts <= maxRetries) {
      try {
        // Check if user is authenticated
        if (!get(isAuthenticated) || !get(accessToken)) {
          console.warn("⚠️ User not authenticated, cannot make API call");
          throw new Error("User not authenticated");
        }

        const result = await apiCall();

        // Log success only on retry (to avoid spam)
        if (attempts > 0) {
          console.log(`✅ API call succeeded on retry attempt ${attempts}`);
        }

        return result;
      } catch (error) {
        attempts++;

        console.log(
          `❌ API call failed (attempt ${attempts}/${maxRetries + 1})`,
        );

        // Only retry on authentication errors and if we haven't exceeded max retries
        if (this.isAuthError(error) && attempts <= maxRetries) {
          console.log("🔄 Detected auth error, attempting token refresh...");

          try {
            // If we're already refreshing, wait for it to complete
            if (this.isRefreshing) {
              console.log("⏳ Token refresh already in progress, waiting...");
              await this.enqueueRequest();
            } else {
              await this.refreshAccessToken();
            }

            console.log("🔄 Token refreshed, retrying API call...");
            // Continue the loop to retry the API call
            continue;
          } catch (refreshError) {
            // If token refresh fails, throw the original error
            console.error("❌ Failed to refresh token, giving up");
            throw error;
          }
        }

        // If it's not an auth error or we've exceeded retries, throw the error
        if (!this.isAuthError(error)) {
          console.log("❌ Non-auth error, not retrying");
        } else {
          console.log("❌ Exceeded max retries, giving up");
        }

        throw error;
      }
    }

    // This should never be reached, but TypeScript requires it
    throw new Error("Unexpected error in executeWithTokenRefresh");
  }

  /**
   * Check if the current access token is likely expired
   * This is a simple check - in a production app you might want to decode the JWT
   */
  isTokenLikelyExpired(): boolean {
    const token = get(accessToken);
    return !token || token === "";
  }
}

// Export a singleton instance
export const tokenManager = new TokenManager();

/**
 * Convenience function to wrap API calls with automatic token refresh
 * Usage: const result = await withTokenRefresh(() => apiCall())
 */
export async function withTokenRefresh<T>(
  apiCall: () => Promise<T>,
  maxRetries: number = 1,
): Promise<T> {
  return tokenManager.executeWithTokenRefresh(apiCall, maxRetries);
}

/**
 * Convenience function specifically for handling ApiException errors
 */
export function isApiAuthError(error: unknown): boolean {
  if (typeof error === "object" && error !== null) {
    // Check for ninja-generated ApiException
    if ("status" in error && error.status === 401) {
      return true;
    }

    // Check for response property with status
    if ("response" in error && error.response) {
      const response = error.response as any;
      if (response.status === 401) {
        return true;
      }
    }

    // Check for body property with status (another common pattern)
    if ("body" in error && error.body) {
      const body = error.body as any;
      if (body.status === 401) {
        return true;
      }
    }
  }

  return false;
}
