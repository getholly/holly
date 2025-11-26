<script lang="ts">
  import { Button, Input, Label, Checkbox } from "flowbite-svelte";
  import { routes } from "$lib/routes";
  import { EyeOutline, EyeSlashOutline } from "flowbite-svelte-icons";
  import { selectedTheme } from "$lib/store/theme.store";
  import { goto } from "$app/navigation";
  import { userEmail } from "$lib/store/auth/tokens.store";
  import { showToast } from "$lib/store/toast/toast.store";
  import { registerUser } from "$lib/apis/auth/api.auth";

  let formError = false;
  let showPassword = false;
  let passwordMismatch = false;
  let agreeToTerms = false;

  function togglePasswordVisibility(event: Event) {
    event.preventDefault();
    showPassword = !showPassword;
  }

  async function register(event: Event) {
    event.preventDefault();

    const formData = new FormData(event.target as HTMLFormElement);
    const email = formData.get("email");
    const password = formData.get("password");

    if (!email || !password) {
      showToast("Email and password are required.", "error");
      return;
    }

    if (!agreeToTerms) {
      showToast(
        "You must agree to the Terms and Conditions and Privacy Policy to create an account.",
        "error",
      );
      return;
    }

    try {
      // Call the register function from api.auth.ts
      await registerUser(email.toString(), password.toString());

      showToast(
        "Registration successful! Please check your email to verify your account.",
        "success",
      );
      userEmail.set(email.toString()); // Store email for potential use on a verification or login page.

      // Redirect to login page after successful registration.
      await goto(routes.login.path);
    } catch (error: any) {
      console.error("Registration error:", error);
      let errorMessage = "An unexpected error occurred during registration.";
      // Try to parse a more specific error message from the API response
      if (error.response && error.response.data) {
        // Assuming the error response structure is { message: "...", detail: "..." } or similar
        errorMessage =
          error.response.data.message ||
          error.response.data.detail ||
          errorMessage;
      } else if (error.message) {
        errorMessage = error.message;
      }
      showToast(errorMessage, "error");
      formError = true;
    }
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
          Create an account
        </h1>
        <form class="space-y-4 md:space-y-6" on:submit={register}>
          <!-- Email Input -->
          <Label class="space-y-2">
            <span>Email</span>
            <Input
              type="email"
              name="email"
              placeholder="Enter your email"
              id="email"
              class="bg-theme-surface focus:border-theme-border focus:outline-0 focus:ring-0 dark:focus:border-theme-primary"
              required
            />
          </Label>

          <!-- Password Input -->
          <div class="space-y-2">
            <span class="text-sm dark:text-gray-200">Password</span>
            <div
              class="align-center flex w-full place-items-center content-center rounded-lg border-1 border-gray-300 bg-gray-100 dark:bg-gray-700 dark:border-gray-600"
            >
              <Input
                type={showPassword ? "text" : "password"}
                name="password"
                placeholder="Enter your password"
                id="password"
                class="border-0 bg-transparent focus:border-theme-primary focus:outline-0 focus:ring-0 dark:focus:border-theme-primary rounded-sm dark:bg-gray-700"
                required
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

          <!-- Terms and Conditions Checkbox -->
          <div class="flex items-start space-x-3">
            <Checkbox
              bind:checked={agreeToTerms}
              class="mt-1 text-theme-primary focus:ring-theme-primary dark:focus:ring-theme-primary"
            />
            <div class="text-sm text-gray-600 dark:text-gray-300">
              I agree to the
              <a
                href={routes.terms.path}
                target="_blank"
                class="text-theme-primary hover:underline dark:text-theme-primary-dark font-medium"
              >
                Terms and Conditions
              </a>
              and
              <a
                href={routes.privacy.path}
                target="_blank"
                class="text-theme-primary hover:underline dark:text-theme-primary-dark font-medium"
              >
                Privacy Policy
              </a>
            </div>
          </div>

          <!-- Error Messages -->
          <div class="min-h-[20px]">
            {#if formError && !passwordMismatch}
              <p
                class="text-red-600 mt-2 flex items-center gap-2 font-semibold"
                aria-live="polite"
              >
                Registration failed! Please check your input.
              </p>
            {/if}
            {#if passwordMismatch}
              <p
                class="text-red-600 mt-2 flex items-center gap-2 font-semibold"
                aria-live="polite"
              >
                Passwords do not match!
              </p>
            {/if}
          </div>

          <!-- Submit Button -->
          <Button
            id="submit-button"
            class="w-full bg-theme-primary duration-300 hover:bg-theme-primary-dark focus:outline-none focus:ring-0 dark:bg-theme-primary dark:hover:bg-theme-primary-dark"
            type="submit"
          >
            Create account
          </Button>
          <div class="text-sm font-medium text-gray-500 dark:text-gray-300">
            Already have an account? <a
              href={routes.login.path}
              class="text-theme-primary hover:underline dark:text-theme-primary-dark"
              >Login here</a
            >
          </div>
        </form>
      </div>
    </div>
  </div>
</section>
