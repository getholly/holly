<script lang="ts">
  import { routes } from "$lib/routes";
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import {
    refreshToken,
    logout as storeLogout,
  } from "$lib/store/auth/tokens.store"; // Aliased logout
  import { get } from "svelte/store";
  import { logoutUser } from "$lib/apis/auth/api.auth";
  import { clearAccessToken } from "$lib/apis/api.config";

  onMount(async () => {
    const currentRefreshToken = get(refreshToken); // Get refreshToken from store before clearing it

    // Call storeLogout to clear Svelte stores first
    storeLogout();

    // Clear access token from API config
    clearAccessToken();

    // Clear cookies manually
    // Cookies.remove("accessToken");
    // Cookies.remove("refreshToken");
    // Cookies.remove("session");

    // Attempt to blacklist the refresh token on the server
    if (currentRefreshToken) {
      try {
        // Call the logout function from api.auth.ts
        await logoutUser(currentRefreshToken);
        console.info("Refresh token blacklisted successfully.");
      } catch (error: any) {
        // Added type for error
        console.warn(
          "Failed to blacklist refresh token:",
          error.message || error,
        );
        // Non-critical error, user is logged out on the client side anyway
      }
    } else {
      console.info("No refresh token found to blacklist.");
    }

    // Redirect to login page
    await goto(routes.login.path);
  });
</script>

<div class="flex items-center justify-center min-h-screen">
  <p class="text-lg dark:text-white">Logging out...</p>
  <!-- Optional: Add a spinner here -->
</div>
