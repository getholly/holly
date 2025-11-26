<script lang="ts">
  import { Button, Checkbox, Input, Label } from "flowbite-svelte";
  import { routes } from "$lib/routes";

  import {
    login as storeLogin,
    loginEmail,
  } from "$lib/store/auth/tokens.store";
  import Cookies from "js-cookie";
  import { loginUser, getUserDetails } from "$lib/apis/auth/api.auth";
  import { setAccessToken } from "$lib/apis/api.config";

  import AlertCircleIcon from "$components/svgs/AlertCircleIcon.svelte";
  import { goto } from "$app/navigation";
  import { EyeOutline, EyeSlashOutline } from "flowbite-svelte-icons";
  import { selectedTheme } from "$lib/store/theme.store";
  import { showToast } from "$lib/store/toast/toast.store";

  let formError = false;
  let showPassword = false;
  let rememberMe = false;

  function togglePasswordVisibility(event: Event) {
    event.preventDefault();
    showPassword = !showPassword;
  }

  function toggleRememberMe() {
    rememberMe = !rememberMe;
  }

  async function login(event: Event) {
    event.preventDefault();

    const formData = new FormData(event.target as HTMLFormElement);
    const email = formData.get("email");
    const password = formData.get("password");

    if (!email || !password) return;

    try {
      // Call the login function from api.auth.ts
      const tokenData = await loginUser(email.toString(), password.toString());

      const newAccessToken = tokenData.access;
      const newRefreshToken = tokenData.refresh;

      // Set access token in API config store to update all API clients with Authorization header
      setAccessToken(newAccessToken);

      // Get user details using the new auth API (now with proper Authorization header)
      const userDetails = await getUserDetails();

      storeLogin(
        userDetails.email,
        userDetails.avatar_url || "", // Ensure avatar_url is handled if null
        newAccessToken,
        newRefreshToken,
      );

      if (rememberMe) {
        loginEmail.set(email.toString());
      }

      await goto(routes.main.path);
    } catch (error: any) {
      console.error("Login error:", error);
      let errorMessage = "An unexpected error occurred. Please try again.";
      if (error.response && error.response.data && error.response.data.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      showToast(errorMessage, "error");
      formError = true;
    }
  }

  function forgotPasswordHandler(e: Event) {
    e.preventDefault();
    goto(routes.forgotPassword.path);
  }
</script>

<section
  class="{$selectedTheme.authBackgroundClass} bg-theme-light-bg dark:bg-theme-dark-bg bg-opacity-60 bg-cover bg-center bg-no-repeat bg-blend-multiply h-full"
>
  <div
    class="pt:mt-0 mx-auto flex flex-col items-center justify-center px-6 py-8 h-full"
  >
    <div
      class="w-full rounded-lg bg-theme-surface shadow dark:bg-theme-surface-dark sm:max-w-md md:mt-0 xl:p-0"
    >
      <div class="space-y-4 p-6 sm:p-8 md:space-y-6 lg:space-y-8">
        <h1
          class="text-center text-xl font-bold leading-tight tracking-tight text-theme-text dark:text-theme-text-inverse md:text-2xl"
        >
          Sign in to your account
        </h1>
        <form class="space-y-4 md:space-y-6" on:submit={login}>
          <Label class="space-y-2">
            <span>Your email</span>
            <Input
              type="email"
              name="email"
              placeholder=""
              autocomplete="username"
              id="username"
              value={$loginEmail}
              class="bg-theme-surface focus:border-theme-border focus:outline-0 focus:ring-0 dark:focus:border-theme-primary"
            />
          </Label>
          <div class="space-y-2">
            <span class="text-sm dark:text-gray-200">Your password</span>
            <div
              class="align-center flex w-full place-items-center content-center rounded-lg border-1 border-theme-border bg-theme-surface dark:bg-theme-surface-dark dark:border-theme-border-dark"
            >
              <Input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder=""
                autocomplete="current-password"
                id="password"
                class="border-0 bg-transparent focus:border-theme-primary focus:outline-0 focus:ring-0 dark:focus:border-theme-primary rounded-sm dark:bg-theme-surface-dark"
              />
              <button
                class="px-2 dark:bg-transparent h-full dark:text-gray-200"
                type="button"
                on:click={togglePasswordVisibility}
              >
                {#if showPassword}
                  <EyeOutline color="grey" class="dark:text-gray-400"
                  ></EyeOutline>
                {:else}
                  <EyeSlashOutline color="grey" class="dark:text-gray-400"
                  ></EyeSlashOutline>
                {/if}
              </button>
            </div>
          </div>
          <div class="flex items-center justify-between">
            <div class="flex items-start">
              <div class="flex h-5 items-center">
                <Checkbox
                  on:click={toggleRememberMe}
                  color={$selectedTheme.defaultColour}
                  >Remember me
                </Checkbox>
              </div>
            </div>
            <div class="flex items-start">
              <div class="flex h-5 items-center">
                <button
                  type="button"
                  on:click={forgotPasswordHandler}
                  class="duration-300 dark:text-theme-text-muted dark:hover:text-theme-text-inverse hover:text-theme-text-secondary text-theme-text-muted"
                  >Forgotten Password?
                </button>
              </div>
            </div>
          </div>
          <div class="">
            {#if formError}
              <p
                class="text-grey-900 mt-2 flex min-h-[20px] items-center gap-2 font-semibold"
                id="test-alert"
              >
                <AlertCircleIcon strokeColour="#EC7357" width="1rem" />
                Invalid credentials! Please try again.
              </p>
            {/if}
          </div>
          <Button
            id="submit-button"
            class="w-full bg-theme-primary  duration-300 hover:bg-theme-primary-dark focus:outline-none focus:ring-0 dark:bg-theme-primary dark:hover:bg-theme-primary-dark "
            type="submit"
            >Log in to your account
          </Button>
          <Button
            on:click={() => goto(routes.register.path)}
            class="w-full bg-transparent dark:bg-transparent text-theme-primary-dark bg-theme-surface dark:bg-theme-dark-bg dark:hover:bg-theme-surface-dark duration-300 hover:bg-theme-border focus:outline-none focus:ring-0 "
            >Create an Account
          </Button>
          <a
            href={$selectedTheme.poweredByLogo.link}
            target="_blank"
            rel="noopener noreferrer"
          >
            <div class="mt-8 flex items-center justify-center gap-2">
              <p
                class="text-center text-sm font-semibold text-theme-text-secondary dark:text-theme-text-inverse"
              >
                Powered By
              </p>
              <img
                class="w-24 invert dark:invert-0"
                src={$selectedTheme.poweredByLogo.src}
                alt="logo"
              />
            </div>
          </a>
        </form>
      </div>
    </div>
  </div>
</section>
