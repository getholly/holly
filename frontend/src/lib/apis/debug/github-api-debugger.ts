import { getGitHubConnectionStatus } from "$lib/apis/users/github-oauth";
import { get } from "svelte/store";
import {
  accessToken,
  refreshToken,
  isAuthenticated,
} from "$lib/store/auth/tokens.store";

/**
 * Debug utility specifically for testing GitHub API calls
 * This can be called from browser console for debugging
 */
export class GitHubApiDebugger {
  /**
   * Test the GitHub connection status API call with full debugging
   */
  static async testGitHubConnectionStatus(): Promise<void> {
    console.log("🧪 Testing GitHub Connection Status API");

    try {
      // Make the API call
      console.log("📞 Making API call...");
      const result = await getGitHubConnectionStatus();

      console.log("✅ API call successful!");
      console.log("📋 Result:", result);
    } catch (error) {
      console.log("❌ API call failed!");
    }
  }

  /**
   * Check if the current tokens look valid
   */
  static validateTokens(): void {
    console.log("🔍 Validating current tokens...");

    const currentAccessToken = get(accessToken);
    const currentRefreshToken = get(refreshToken);
    const currentIsAuthenticated = get(isAuthenticated);

    console.log("Authentication Status:", currentIsAuthenticated);

    if (!currentAccessToken) {
      console.warn("⚠️ No access token found!");
      return;
    }

    if (!currentRefreshToken) {
      console.warn("⚠️ No refresh token found!");
    }

    // Try to decode JWT tokens (basic validation)
    this.validateJWT(currentAccessToken, "Access Token");

    if (currentRefreshToken) {
      this.validateJWT(currentRefreshToken, "Refresh Token");
    }
  }

  /**
   * Basic JWT validation and info extraction
   */
  private static validateJWT(token: string, tokenType: string): void {
    try {
      const parts = token.split(".");

      if (parts.length !== 3) {
        console.error(
          `❌ ${tokenType}: Invalid JWT format (should have 3 parts)`,
        );
        return;
      }

      // Decode header
      const header = JSON.parse(atob(parts[0]));
      console.log(`📋 ${tokenType} Header:`, header);

      // Decode payload
      const payload = JSON.parse(atob(parts[1]));
      console.log(`📋 ${tokenType} Payload:`, payload);

      // Check expiration
      if (payload.exp) {
        const expirationDate = new Date(payload.exp * 1000);
        const now = new Date();
        const isExpired = expirationDate < now;

        console.log(`⏰ ${tokenType} Expires:`, expirationDate.toISOString());
        console.log(`⏰ Current Time:`, now.toISOString());
        console.log(
          `${isExpired ? "❌" : "✅"} ${tokenType} ${isExpired ? "EXPIRED" : "Valid"}`,
        );

        if (!isExpired) {
          const timeUntilExpiry = expirationDate.getTime() - now.getTime();
          const minutesUntilExpiry = Math.floor(timeUntilExpiry / (1000 * 60));
          console.log(
            `⏳ ${tokenType} expires in ${minutesUntilExpiry} minutes`,
          );
        }
      }
    } catch (error) {
      console.error(`❌ Failed to decode ${tokenType}:`, error);
    }
  }

  /**
   * Make a raw fetch request to the API endpoint for debugging
   */
  static async testRawAPICall(): Promise<void> {
    console.log("🧪 Testing raw API call to GitHub connection status");

    const currentAccessToken = get(accessToken);

    if (!currentAccessToken) {
      console.error("❌ No access token available for raw API call");
      return;
    }

    const apiUrl = "http://localhost:8000/_api/users/github/connection-status";

    try {
      console.log("📞 Making raw fetch request to:", apiUrl);

      const response = await fetch(apiUrl, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${currentAccessToken}`,
          "Content-Type": "application/json",
        },
        credentials: "include",
      });

      console.log("📊 Response Status:", response.status);
      console.log(
        "📊 Response Headers:",
        Object.fromEntries(response.headers.entries()),
      );

      if (response.ok) {
        const data = await response.json();
        console.log("✅ Raw API call successful!");
        console.log("📋 Response Data:", data);
      } else {
        const errorText = await response.text();
        console.log("❌ Raw API call failed!");
        console.log("📋 Error Response:", errorText);
      }
    } catch (error) {
      console.error("❌ Raw API call error:", error);
    }
  }
}

// Make it available in browser console
if (typeof window !== "undefined") {
  (window as any).GitHubApiDebugger = GitHubApiDebugger;
  console.log("🔧 GitHubApiDebugger available in console. Try:");
  console.log("  GitHubApiDebugger.testGitHubConnectionStatus()");
  console.log("  GitHubApiDebugger.validateTokens()");
  console.log("  GitHubApiDebugger.testRawAPICall()");
}

export default GitHubApiDebugger;
