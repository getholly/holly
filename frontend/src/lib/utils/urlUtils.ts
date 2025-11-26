import { routes, type RouteKey } from "$lib/routes";

/**
 * Generates a URL based on the route key and parameters.
 *
 * @param routeKey - The key of the route from the routes configuration.
 * @param params - An object containing the parameters for the route.
 * @returns The generated URL.
 */
export function generateUrl(
  routeKey: RouteKey,
  params: Record<string, string | number>,
): string {
  const route = routes[routeKey];
  if (!route) {
    throw new Error(`Route ${routeKey} not found`);
  }

  let path = route.path;

  for (const [key, value] of Object.entries(params)) {
    path = path.replace(`:${key}`, encodeURIComponent(String(value)));
  }

  return path;
}
