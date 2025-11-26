import type {
  Middleware,
  RequestContext,
  ResponseContext,
  ErrorContext,
} from "holly-api";
import { get } from "svelte/store";
import {
  accessToken,
  refreshToken as refreshTokenStore,
  logout,
} from "$lib/store/auth/tokens.store";
import { refreshTokenAndUpdateConfig } from "$lib/apis/auth/api.auth";
import { goto } from "$app/navigation";
import { routes } from "$lib/routes";

/**
 * Middleware that automatically handles 401 responses by refreshing tokens
 * and retrying the original request. Maximum of 2 retries to prevent infinite loops.
 */
class TokenRefreshMiddleware implements Middleware {
  private retryMap = new WeakMap<RequestContext, number>();

  /**
   * Handle response and check for 401 errors
   */
  async post(context: ResponseContext): Promise<Response | void> {
    // Only handle 401 responses
    if (context.response.status !== 401) {
      return;
    }

    // Get current retry count for this request
    const retryCount = this.retryMap.get(context) || 0;

    // Max 2 retries to prevent infinite loops
    if (retryCount >= 2) {
      console.warn("🔄 Max token refresh retries (2) exceeded, giving up");
      this.handleTokenRefreshFailure();
      return;
    }

    console.log(
      `🔄 Detected 401 response, attempting token refresh (attempt ${retryCount + 1}/2)`,
    );

    try {
      await this.refreshAccessToken();

      // Increment retry count
      this.retryMap.set(context, retryCount + 1);

      // Retry the original request with new token
      console.log("🔄 Token refreshed successfully, retrying original request");
      return this.retryOriginalRequest(context);
    } catch (error) {
      console.error("❌ Token refresh failed:", error);
      this.handleTokenRefreshFailure();
      return;
    }
  }

  /**
   * Handle errors that might occur during the request
   */
  async onError(context: ErrorContext): Promise<Response | void> {
    // Check if the error is related to 401/authentication
    if (this.isAuthenticationError(context.error)) {
      // Get current retry count for this request
      const retryCount = this.retryMap.get(context) || 0;

      // Max 2 retries to prevent infinite loops
      if (retryCount >= 2) {
        console.warn(
          "🔄 Max token refresh retries (2) exceeded during error handling",
        );
        this.handleTokenRefreshFailure();
        return;
      }

      console.log(
        `🔄 Detected auth error, attempting token refresh (attempt ${retryCount + 1}/2)`,
      );

      try {
        await this.refreshAccessToken();

        // Increment retry count
        this.retryMap.set(context, retryCount + 1);

        // Retry the original request
        console.log(
          "🔄 Token refreshed successfully, retrying original request",
        );
        return this.retryOriginalRequestFromError(context);
      } catch (error) {
        console.error("❌ Token refresh failed during error handling:", error);
        this.handleTokenRefreshFailure();
        return;
      }
    }

    // Not an auth error, let it propagate
    return;
  }

  /**
   * Refresh the access token using the stored refresh token
   */
  private async refreshAccessToken(): Promise<void> {
    const currentRefreshToken = get(refreshTokenStore);

    if (!currentRefreshToken) {
      throw new Error("No refresh token available");
    }

    try {
      // Use the existing refresh function that updates the store
      await refreshTokenAndUpdateConfig(currentRefreshToken);
      console.log("✅ Access token refreshed successfully");
    } catch (error) {
      console.error("❌ Failed to refresh access token:", error);
      throw error;
    }
  }

  /**
   * Retry the original request with the new token
   */
  private async retryOriginalRequest(
    context: ResponseContext,
  ): Promise<Response> {
    // Get the current access token (should be updated after refresh)
    const newToken = get(accessToken);

    // Clone the original headers and update the Authorization header
    const updatedHeaders = new Headers(context.init.headers);
    if (newToken) {
      updatedHeaders.set("Authorization", `Bearer ${newToken}`);
    }

    // Create a new request with the updated headers
    const newRequest = new Request(context.url, {
      method: context.init.method,
      headers: updatedHeaders,
      body: context.init.body,
      credentials: context.init.credentials,
      mode: context.init.mode,
      cache: context.init.cache,
      redirect: context.init.redirect,
      referrer: context.init.referrer,
      referrerPolicy: context.init.referrerPolicy,
      integrity: context.init.integrity,
      keepalive: context.init.keepalive,
      signal: context.init.signal,
    });

    return context.fetch(newRequest);
  }

  /**
   * Retry the original request from an error context
   */
  private async retryOriginalRequestFromError(
    context: ErrorContext,
  ): Promise<Response> {
    // Get the current access token (should be updated after refresh)
    const newToken = get(accessToken);

    // Clone the original headers and update the Authorization header
    const updatedHeaders = new Headers(context.init.headers);
    if (newToken) {
      updatedHeaders.set("Authorization", `Bearer ${newToken}`);
    }

    // Create a new request with the updated headers
    const newRequest = new Request(context.url, {
      method: context.init.method,
      headers: updatedHeaders,
      body: context.init.body,
      credentials: context.init.credentials,
      mode: context.init.mode,
      cache: context.init.cache,
      redirect: context.init.redirect,
      referrer: context.init.referrer,
      referrerPolicy: context.init.referrerPolicy,
      integrity: context.init.integrity,
      keepalive: context.init.keepalive,
      signal: context.init.signal,
    });

    return context.fetch(newRequest);
  }

  /**
   * Check if an error is related to authentication
   */
  private isAuthenticationError(error: unknown): boolean {
    if (typeof error === "object" && error !== null) {
      // Check for Response object with 401 status
      if ("status" in error && error.status === 401) {
        return true;
      }

      // Check for fetch Response in error
      if ("response" in error && error.response) {
        const response = error.response as any;
        if (response.status === 401) {
          return true;
        }
      }

      // Check for error message containing auth-related terms
      if ("message" in error && typeof error.message === "string") {
        const message = error.message.toLowerCase();
        return (
          message.includes("401") ||
          message.includes("unauthorized") ||
          message.includes("authentication")
        );
      }
    }

    return false;
  }

  /**
   * Handle token refresh failure by logging out user and redirecting to login
   */
  private handleTokenRefreshFailure(): void {
    console.warn(
      "🚫 Token refresh failed, logging out user and redirecting to login",
    );

    // Log out the user (clears tokens and auth state)
    logout();

    // Redirect to login page
    // Use setTimeout to avoid navigation during middleware execution
    setTimeout(() => {
      goto(routes.login.path);
    }, 0);
  }
}

// Export singleton instance
export const tokenRefreshMiddleware = new TokenRefreshMiddleware();
