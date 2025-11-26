import { persistableStore } from "$lib/store/persistable.store";
import { writable } from "svelte/store";

export const accessToken = persistableStore("accessToken", "");
export const refreshToken = persistableStore("refreshToken", "");
export const popupModalRelogin = writable(false);
export const avatarUrl = persistableStore("avatarUrl", "");

export const isAuthenticated = persistableStore("isAuthenticated", false);
// used to store/remember the user's login email
export const loginEmail = persistableStore("loginEmail", "");
export const userEmail = persistableStore("userEmail", "");

export const logout = () => {
  accessToken.set("");
  refreshToken.set("");
  isAuthenticated.set(false);
  userEmail.set("");
  avatarUrl.set("");
};

export const login = (
  email: string,
  newAvatarUrl: string,
  newAccessToken: string,
  newRefreshToken: string,
) => {
  loginEmail.set(email);
  userEmail.set(email);
  avatarUrl.set(newAvatarUrl);
  accessToken.set(newAccessToken);
  refreshToken.set(newRefreshToken);
  isAuthenticated.set(true);
};
