/**
 * Open-redirect guard.
 *
 * Returns the given target only if it is a safe, same-origin *path* (starts with
 * a single "/" and is not a protocol-relative "//host" or absolute "scheme://"
 * URL). Anything else falls back to `fallback`. This prevents attacker-supplied
 * redirect targets (e.g. via an OAuth `state.redirect_url` or a `?redirect=`
 * query param) from sending users to an external origin.
 */
export function safeRedirectPath(target: unknown, fallback = "/"): string {
  if (typeof target !== "string" || target.length === 0) {
    return fallback;
  }
  // Must be an absolute internal path, but not protocol-relative ("//evil.com")
  // and not a backslash variant ("/\evil.com") that some browsers normalize.
  if (!target.startsWith("/") || target.startsWith("//") || target.startsWith("/\\")) {
    return fallback;
  }
  // Reject anything that smuggles a scheme (e.g. "/redirect?next=https://...").
  if (/^\/[^/]*:/.test(target)) {
    return fallback;
  }
  return target;
}
