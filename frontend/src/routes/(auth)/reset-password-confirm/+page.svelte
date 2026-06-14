<script lang="ts">
  import { Button, Input, Label } from "flowbite-svelte";
  import { selectedTheme } from "$lib/store/theme.store";
  import { routes } from "$lib/routes";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { showToast } from "$lib/store/toast/toast.store";
  import {
    confirmPasswordReset,
    loginUser,
    getUserDetails,
  } from "$lib/apis/auth/api.auth";
  import { setAccessToken } from "$lib/apis/api.config";
  import { login as storeLogin } from "$lib/store/auth/tokens.store";

  let formSubmitted = false;
  let newPassword = "";
  let confirmNewPassword = "";
  let isSubmitting = false;
  let uidb64 = "";
  let token = "";

  onMount(() => {
    // const urlParams = new URLSearchParams($page.url.search);
    // uidb64 = urlParams.get("uidb64") || "";
    // token = urlParams.get("token") || "";
    uidb64 = $page.url.searchParams.get("uidb64") || "";
    token = $page.url.searchParams.get("token") || "";

    if (!uidb64 || !token) {
      showToast(
        "Invalid or missing password reset parameters in URL.",
        "error",
      );
      goto(routes.forgotPassword.path);
    }
  });

  async function handleSubmit(event: Event) {
    event.preventDefault();

    if (newPassword.length < 8) {
      showToast("Password must be at least 8 characters long!", "error");
      return;
    }

    if (newPassword !== confirmNewPassword) {
      showToast("Passwords do not match!", "error");
      return;
    }

    isSubmitting = true;

    try {
      // Call the password reset confirm function from api.auth.ts
      const resetResponse = await confirmPasswordReset(
        uidb64,
        token,
        newPassword,
      );

      showToast(
        "Password has been reset successfully! Logging you in...",
        "success",
      );

      // Auto-login with the new password
      try {
        // Extract email from the response (after we update the backend to return it)
        // For now, we'll need to get the email some other way or ask user to login manually

        // If the backend returns the email in the response, we can use it:
        const userEmail = resetResponse.email || null;

        if (userEmail) {
          // Attempt auto-login with new password
          const tokenData = await loginUser(userEmail, newPassword);

          // Set access token in API config
          setAccessToken(tokenData.access);

          // Get user details and update store
          const userDetails = await getUserDetails();
          storeLogin(
            userDetails.email,
            userDetails.username,
            userDetails.avatar_url || "",
            tokenData.access,
            tokenData.refresh,
          );

          showToast("Successfully logged in! Redirecting...", "success");
          setTimeout(() => {
            goto(routes.main.path);
          }, 1500);
        } else {
          // Fallback to login page if we can't auto-login
          formSubmitted = true;
          setTimeout(() => {
            showToast("Please log in with your new password.", "info");
            goto(routes.login.path);
          }, 2000);
        }
      } catch (loginError) {
        // If auto-login fails, still show success and redirect to login
        console.warn("Auto-login failed after password reset:", loginError);
        formSubmitted = true;
        setTimeout(() => {
          showToast(
            "Password reset successful! Please log in with your new password.",
            "info",
          );
          goto(routes.login.path);
        }, 2000);
      }
    } catch (error: any) {
      console.error("Reset password error:", error);
      let errorMessage = "An unexpected error occurred. Please try again.";
      if (error.response && error.response.data) {
        errorMessage =
          error.response.data.message ||
          error.response.data.detail ||
          errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      showToast(errorMessage, "error");
    } finally {
      isSubmitting = false;
    }
  }
</script>

<section
  class="{$selectedTheme.authBackgroundClass} bg-gray-700 bg-opacity-60 bg-cover bg-center bg-no-repeat bg-blend-multiply"
>
  <div
    class="pt:mt-0 mx-auto flex flex-col items-center justify-center px-6 py-8 md:h-screen"
  >
    <span class="mb-6 flex items-center text-2xl font-semibold text-white">
      <img
        class="w-40"
        src={$selectedTheme.logo.src}
        alt={$selectedTheme.logo.alt}
      />
    </span>
    <div
      class="w-full rounded-lg bg-white shadow dark:bg-gray-800 sm:max-w-md md:mt-0 xl:p-0"
    >
      <div class="space-y-4 p-6 sm:p-8 md:space-y-6 lg:space-y-8">
        {#if formSubmitted}
          <div
            class="space-y-4 p-6 sm:p-8 md:space-y-6 lg:space-y-8 text-center"
          >
            <h1
              class="text-2xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white"
            >
              Password Updated Successfully!
            </h1>
            <p class="text-gray-700 dark:text-gray-300">
              Your password has been successfully reset and you are being logged
              in automatically.
            </p>
            <Button
              on:click={() => goto(routes.login.path)}
              class="w-full bg-theme-primary duration-300 hover:bg-theme-secondary mt-6"
            >
              Go to Login
            </Button>
          </div>
        {:else}
          <h1
            class="text-center text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Set Your New Password
          </h1>
          <p class="text-sm text-gray-600 dark:text-gray-400 text-center">
            Please enter your new password below. Make sure it's secure and you
            remember it.
          </p>
          <form class="space-y-4 md:space-y-6" on:submit={handleSubmit}>
            <Label class="space-y-2">
              <span class="text-gray-700 dark:text-gray-300">New Password</span>
              <Input
                type="password"
                name="newPassword"
                placeholder="••••••••"
                bind:value={newPassword}
                required
                minlength="8"
                class="bg-gray-100 focus:border-gray-300 focus:outline-0 focus:ring-0 dark:focus:border-theme-primary"
              />
            </Label>
            <Label class="space-y-2">
              <span class="text-gray-700 dark:text-gray-300"
                >Confirm New Password</span
              >
              <Input
                type="password"
                name="confirmNewPassword"
                placeholder="••••••••"
                bind:value={confirmNewPassword}
                required
                minlength="8"
                class="bg-gray-100 focus:border-gray-300 focus:outline-0 focus:ring-0 dark:focus:border-theme-primary"
              />
            </Label>
            <Button
              class="w-full bg-theme-primary duration-300 hover:bg-theme-secondary focus:ring-0"
              type="submit"
              disabled={isSubmitting}
            >
              {isSubmitting ? "Resetting Password..." : "Reset Password"}
            </Button>
          </form>
          {#if !formSubmitted}
            <p
              class="text-center text-sm font-light text-gray-500 dark:text-gray-400"
            >
              Remembered your password or need to request a new link?
              <a
                href={routes.login.path}
                class="font-medium text-theme-primary hover:underline dark:text-theme-primary-dark"
              >
                Back to login
              </a>
            </p>
          {/if}
        {/if}
      </div>
    </div>
  </div>
</section>
