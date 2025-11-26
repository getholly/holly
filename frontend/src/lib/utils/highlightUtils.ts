import { H } from "highlight.run";
import { baseURL } from "$lib/apis/api.config";

export function updateHighlightIdentity(email: string) {
  console.debug("Updating Highlight Identity");
  H.identify(email.toString(), {
    server: baseURL,
  });
}
