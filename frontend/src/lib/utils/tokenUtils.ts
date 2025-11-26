// import {authApi} from "$lib/apis/api.config"
// import {routes} from "$lib/routes"
// import {redirect} from "@sveltejs/kit"
// import type {RefreshAuthJwtRefreshPostRequest} from "holly-api";
//
// interface JWTToken {
//     token_type: string
//     iat: number
//     exp: number
//     jti: string
//     public_id: string
//     email: string
// }
//
// export function parseJWT(token: string): JWTToken {
//     const base64Url = token.split(".")[1]
//     const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/")
//     const jsonPayload = decodeURIComponent(
//         window
//             .atob(base64)
//             .split("")
//             .map(function (c) {
//                 return "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2)
//             })
//             .join("")
//     )
//
//     return JSON.parse(jsonPayload)
// }
//
// export const isAccessTokenExpired = (token: JWTToken) => {
//     const currentTimestamp = Math.floor(Date.now() / 1000)
//     return currentTimestamp > token.exp
// }
//
// export const refreshAccessToken = async (
//     a_refreshToken: string
// ): Promise<string> => {
//     console.info("Attempting to refresh access token ...")
//     if (!a_refreshToken) throw redirect(303, routes.logout.path)
//
//     try {
//         const req: RefreshAuthJwtRefreshPostRequest = {
//             refreshTokenType: {
//                 refresh_token: a_refreshToken,
//             },
//         }
//
//         const apiToken = await authApi.refreshAuthJwtRefreshPost(req)
//         return apiToken.access_token
//     } catch (err) {
//         console.error("Error with token refresh", err)
//         throw redirect(303, routes.logout.path)
//     }
// }

import { writable } from "svelte/store";

export const csrfToken = writable("");

export function getCSRFToken(): string {
  if (typeof document === "undefined") {
    return "";
  }

  const name = "csrftoken=";
  const decodedCookie = decodeURIComponent(document.cookie);
  const cookieArray = decodedCookie.split(";");

  for (let cookie of cookieArray) {
    cookie = cookie.trim();
    if (cookie.indexOf(name) === 0) {
      const token = cookie.substring(name.length);
      csrfToken.set(token);
      return token;
    }
  }

  return "";
}
