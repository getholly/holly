<script lang="ts">
  import { Button, Input, Label } from "flowbite-svelte";
  import { selectedTheme } from "$lib/store/theme.store";
  import { routes } from "$lib/routes";
  import { goto } from "$app/navigation";
  import { showToast } from "$lib/store/toast/toast.store";
  import { requestPasswordReset } from "$lib/apis/auth/api.auth";

  let formSubmitted = false;
  let email = ""; // Bind email input

  async function handleSubmit(event: Event) {
    event.preventDefault();

    if (!email) {
      showToast("Please enter your email address.", "error");
      return;
    }

    try {
      // Call the password reset request function from api.auth.ts
      await requestPasswordReset(email);

      formSubmitted = true;
      showToast(
        "Password reset email sent successfully. Please check your inbox.",
        "success",
      );
    } catch (error: any) {
      console.error("Forgot password error:", error);
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
          <div class="space-y-4 p-6 sm:p-8 md:space-y-6 lg:space-y-8">
            <h1
              class="text-center text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
            >
              Email Sent
            </h1>
            <p class="text-gray-700 dark:text-gray-300">
              We have sent an email to <strong>{email}</strong> with a link to reset
              your password. Please check your inbox and spam folder.
            </p>
            <Button
              class="w-full bg-theme-primary duration-300 hover:bg-theme-secondary mt-4"
              on:click={() => goto(routes.login.path)}
            >
              Back to Login
            </Button>
          </div>
        {:else}
          <h1
            class="text-center text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
          >
            Forgot Your Password?
          </h1>
          <p class="text-sm text-gray-600 dark:text-gray-400 text-center">
            No problem! Enter your email address below and we'll send you a link
            to reset your password.
          </p>
          <form class="space-y-4 md:space-y-6" on:submit={handleSubmit}>
            <Label class="space-y-2">
              <span class="text-gray-700 dark:text-gray-300">Your email</span>
              <Input
                type="email"
                name="email"
                placeholder="name@getholly.ai"
                bind:value={email}
                required
                class="bg-gray-100 focus:border-gray-300 focus:outline-0 focus:ring-0 dark:focus:border-theme-primary"
              />
            </Label>
            <Button
              class="w-full bg-theme-primary duration-300 hover:bg-theme-secondary focus:ring-0"
              type="submit"
            >
              Send Reset Link
            </Button>
          </form>
          <p
            class="text-center text-sm font-light text-gray-500 dark:text-gray-400"
          >
            Remembered your password?
            <a
              href={routes.login.path}
              class="font-medium text-theme-primary hover:underline dark:text-theme-primary-dark"
            >
              Back to login
            </a>
          </p>
        {/if}
      </div>
    </div>
  </div>
</section>
