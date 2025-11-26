<script lang="ts">
  import { Button } from "flowbite-svelte";
  import { selectedTheme } from "$lib/store/theme.store";
  import { routes } from "$lib/routes";
  import { page } from "$app/stores";
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { showToast } from "$lib/store/toast/toast.store";

  let hasTokenParams = false;

  onMount(() => {
    const urlParams = new URLSearchParams($page.url.search);
    const uidb64 = urlParams.get("uidb64");
    const token = urlParams.get("token");

    if (uidb64 && token) {
      // If this page has token parameters, redirect to the confirm page
      hasTokenParams = true;
      const confirmUrl = `${routes.resetPasswordConfirm.path}?uidb64=${uidb64}&token=${token}`;
      goto(confirmUrl);
    } else {
      // This page was accessed without tokens, just show info message
      hasTokenParams = false;
    }
  });
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
        {#if hasTokenParams}
          <div class="text-center">
            <h1
              class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
            >
              Redirecting...
            </h1>
            <p class="text-gray-600 dark:text-gray-400">
              You are being redirected to set your new password.
            </p>
          </div>
        {:else}
          <div class="text-center space-y-4">
            <h1
              class="text-xl font-bold leading-tight tracking-tight text-gray-900 dark:text-white md:text-2xl"
            >
              Password Reset
            </h1>
            <p class="text-gray-600 dark:text-gray-400">
              To reset your password, please use the link sent to your email
              address.
            </p>
            <p class="text-gray-600 dark:text-gray-400">
              If you haven't received an email, you can request a new password
              reset link.
            </p>
            <div class="space-y-3">
              <Button
                on:click={() => goto(routes.forgotPassword.path)}
                class="w-full bg-theme-primary duration-300 hover:bg-theme-secondary"
              >
                Request New Reset Link
              </Button>
              <Button
                on:click={() => goto(routes.login.path)}
                class="w-full bg-gray-500 duration-300 hover:bg-gray-600"
              >
                Back to Login
              </Button>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
</section>
