<script lang="ts">
  import { Button } from "flowbite-svelte";
  import { selectedTheme } from "$lib/store/theme.store";
  import { userEmail } from "$lib/store/auth/tokens.store"; // To get user's email for resend
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { routes } from "$lib/routes";
  import { showToast } from "$lib/store/toast/toast.store"; // Import routes for navigation

  // import {
  // 	resendVerification, // Old API call
  // 	userSignupVerifyEmailToken, // Old API call
  // } from "$lib/apis/auth/api.auth";

  let verificationStatus: "pending" | "success" | "error" | "initial" =
    "initial"; // initial, pending, success, error
  let token: string | null = null;
  let isResending = false;

  onMount(async () => {
    const urlParams = new URLSearchParams($page.url.search);
    token = urlParams.get("token");

    if (token) {
      verificationStatus = "pending";
      try {
        const response = await fetch(`/api/auth/verify-email/`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ token }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          const message =
            errorData.detail ||
            errorData.message ||
            "Email verification failed. The token may be invalid or expired.";
          showToast(message, "error");
          verificationStatus = "error";
          return;
        }
        // const data = await response.json(); // If response contains useful data
        showToast("Email verified successfully!", "success");
        verificationStatus = "success";
      } catch (error) {
        console.error("Error verifying token:", error);
        showToast("An unexpected error occurred during verification.", "error");
        verificationStatus = "error";
      }
    } else {
      // This case is if the page is loaded without a token.
      // It could be that the user navigated here from the registration success message.
      verificationStatus = "initial"; // No token, waiting for user to potentially resend.
    }
  });

  async function resendVerificationEmail() {
    if (!$userEmail) {
      showToast(
        "No email address found to resend verification. Please log in or register again.",
        "error",
      );
      return;
    }
    isResending = true;
    try {
      const response = await fetch(`/api/auth/verify-email/resend/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ email: $userEmail }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        const message =
          errorData.detail ||
          errorData.message ||
          "Failed to resend verification email.";
        showToast(message, "error");
        isResending = false;
        return;
      }
      showToast(
        "Verification email resent successfully. Please check your inbox.",
        "success",
      );
    } catch (error) {
      console.error("Error resending verification email:", error);
      showToast(
        "An unexpected error occurred while resending the email.",
        "error",
      );
    } finally {
      isResending = false;
    }
  }

  function goToLogin() {
    goto(routes.login.path);
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
      <div class="space-y-4 p-6 sm:p-8 md:space-y-6 lg:space-y-8 text-center">
        {#if verificationStatus === "pending"}
          <h1
            class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Verifying Email...
          </h1>
          <p class="text-gray-600 dark:text-gray-200">
            Please wait while we verify your email address.
          </p>
          <!-- Optional: Add a spinner here -->
        {:else if verificationStatus === "success"}
          <h1
            class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Email Verified Successfully!
          </h1>
          <p class="text-gray-600 dark:text-gray-200">
            Your email has been verified. You can now log in with your account.
          </p>
          <Button
            class="mt-4 w-full bg-theme-primary duration-300 hover:bg-theme-secondary"
            on:click={goToLogin}
          >
            Go to Login
          </Button>
        {:else if verificationStatus === "error"}
          <h1
            class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Email Verification Failed
          </h1>
          <p class="text-red-600 dark:text-red-400">
            The verification link may be invalid, expired, or already used. You
            can try resending the verification email.
          </p>
          <Button
            class="mt-4 text-gray-800 bg-gray-200 duration-300 hover:bg-gray-300 focus:outline-none focus:ring-0 dark:text-white dark:bg-theme-secondary dark:hover:bg-theme-primary"
            on:click={resendVerificationEmail}
            disabled={isResending}
          >
            {isResending ? "Resending..." : "Resend Verification Email"}
          </Button>
          <Button
            class="mt-2 w-full bg-theme-primary duration-300 hover:bg-theme-secondary"
            on:click={goToLogin}
          >
            Back to Login
          </Button>
        {:else}
          <!-- verificationStatus === "initial" -->
          <h1
            class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Verify Your Email Address
          </h1>
          <p class="text-gray-600 dark:text-gray-200">
            If you received a verification link, please click it. Otherwise, you
            can request a new verification email. Your email: {$userEmail ||
              "Not available. Please register again if needed."}
          </p>
          <Button
            class="mt-4 text-gray-800 bg-gray-200 duration-300 hover:bg-gray-300 focus:outline-none focus:ring-0 dark:text-white dark:bg-theme-secondary dark:hover:bg-theme-primary"
            on:click={resendVerificationEmail}
            disabled={isResending || !$userEmail}
          >
            {isResending ? "Resending..." : "Resend Verification Email"}
          </Button>
          <Button
            class="mt-2 w-full bg-theme-primary duration-300 hover:bg-theme-secondary"
            on:click={goToLogin}
          >
            Go to Login
          </Button>
        {/if}
      </div>
    </div>
  </div>
</section>
