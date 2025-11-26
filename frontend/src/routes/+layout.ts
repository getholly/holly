import type { LayoutLoad } from "./$types";
import { goto } from "$app/navigation";
import { browser } from "$app/environment";
import { isAuthenticated } from "$lib/store/auth/tokens.store";
import { routes } from "$lib/routes";
import { get } from "svelte/store";

export const ssr = false; // Disable server-side rendering for our app

// Define public routes that do not require authentication
// Ensure paths here match exactly how they are defined in routes.ts and used in navigation
const publicRoutes = [
  routes.login.path, // e.g., /auth/login
  routes.register.path, // e.g., /auth/register
  routes.forgotPassword.path, // e.g., /auth/forgot-password
  routes.resetPassword.path, // e.g., /auth/reset-password
  routes.resetPasswordConfirm.path, // e.g., /auth/reset-password-confirm
  routes.verifyEmail.path, // e.g., /auth/verify-email
  routes.terms.path, // Terms and Conditions page
  routes.privacy.path, // Privacy Policy page
  "/", // Landing page at root
  // Add any other public static paths like marketing pages if necessary.
  // For example, if you have a public landing page at the root:
  // '/',
  // Or specific public informational pages:
  // '/about-us',
  // '/contact',
];

// It's crucial to ensure that `routes.main.path` is NOT in publicRoutes if it requires auth.
// Typically, routes.main.path would be something like '/dashboard' or '/app'.
// If '/' is the main authenticated page, then it should not be in publicRoutes.
// For this example, let's assume '/' is a generic landing/marketing page and is public.
// If your main app page IS '/', then remove it from publicRoutes.

export const load: LayoutLoad = async ({ url }) => {
  if (!browser) {
    // If not in browser, cookies aren't accessible in the same way.
    // SSR route protection would typically be handled in hooks.server.ts by checking HTTP-only cookies
    // or by other means if JWT is passed differently for SSR.
    // Since we're using js-cookie, this check is primarily client-side.
    return {};
  }

  const currentPath = url.pathname;

  // Check if the current path is one of the defined public routes.
  // This handles exact matches. For paths with parameters or wildcard, more complex matching might be needed.
  const isPublicRoute = publicRoutes.includes(currentPath);

  if (!get(isAuthenticated) && !isPublicRoute) {
    console.log(
      `[Layout Load] User not authenticated, trying to access restricted page: ${currentPath}. Redirecting to login.`,
    );
    // Preserve the original path for redirection after login, excluding the base path if necessary.
    const redirectTo = currentPath + url.search; // Keep query params
    await goto(
      routes.login.path + `?redirect=${encodeURIComponent(redirectTo)}`,
    );
    return {}; // Prevent rendering of the current page before redirect
  }

  if (
    get(isAuthenticated) &&
    (currentPath === routes.login.path || currentPath === routes.register.path)
  ) {
    console.log(
      `[Layout Load] User authenticated, trying to access ${currentPath}. Redirecting to main page: ${routes.main.path}`,
    );
    await goto(routes.main.path);
    return {}; // Prevent rendering
  }

  // Allow access if:
  // 1. User is authenticated and accessing a non-login/register page.
  // 2. User is not authenticated but accessing a public route.
  return {};
};
