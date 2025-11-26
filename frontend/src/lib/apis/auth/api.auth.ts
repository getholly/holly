import {
  authApi,
  authenticationApi,
  setAccessToken,
} from "$lib/apis/api.config";
import { get } from "svelte/store";
import type {
  AuthApi,
  AuthenticationApi,
  TokenObtainPairInputSchema,
  TokenObtainPairOutputSchema,
  TokenRefreshInputSchema,
  TokenRefreshOutputSchema,
  UserSignupSchema,
  UserResponseSchema,
  UserDetailSchema,
  PasswordResetRequestSchema,
  PasswordResetConfirmSchema,
  RefreshTokenSchema,
  MessageSchema,
} from "holly-api";

function getAuthApiClient(): AuthApi {
  return get(authApi);
}

function getAuthenticationApiClient(): AuthenticationApi {
  return get(authenticationApi);
}

export async function loginUser(
  email: string,
  password: string,
): Promise<TokenObtainPairOutputSchema> {
  try {
    const tokenObtainPairInputSchema: TokenObtainPairInputSchema = {
      email: email,
      password: password,
    };

    return await getAuthApiClient().tokenObtainPair({
      tokenObtainPairInputSchema,
    });
  } catch (error) {
    throw error;
  }
}

export async function refreshToken(
  refreshToken: string,
): Promise<TokenRefreshOutputSchema> {
  try {
    const tokenRefreshInputSchema: TokenRefreshInputSchema = {
      refresh: refreshToken,
    };

    return await getAuthApiClient().tokenRefresh({
      tokenRefreshInputSchema,
    });
  } catch (error) {
    throw error;
  }
}

export async function refreshTokenAndUpdateConfig(
  refreshToken: string,
): Promise<TokenRefreshOutputSchema> {
  try {
    const tokenRefreshInputSchema: TokenRefreshInputSchema = {
      refresh: refreshToken,
    };

    const result = await getAuthApiClient().tokenRefresh({
      tokenRefreshInputSchema,
    });

    // Update the API config with the new access token
    setAccessToken(result.access);

    return result;
  } catch (error) {
    throw error;
  }
}

export async function registerUser(
  email: string,
  password: string,
): Promise<UserResponseSchema> {
  try {
    const userSignupSchema: UserSignupSchema = {
      email: email,
      password: password,
    };

    return await getAuthenticationApiClient().hollyHollyApiCustomAuthViewsRegister(
      {
        userSignupSchema,
      },
    );
  } catch (error) {
    throw error;
  }
}

export async function getUserDetails(): Promise<UserDetailSchema> {
  try {
    return await getAuthenticationApiClient().hollyHollyApiCustomAuthViewsGetUserDetails();
  } catch (error) {
    throw error;
  }
}

export async function logoutUser(refreshToken: string): Promise<MessageSchema> {
  try {
    const refreshTokenSchema: RefreshTokenSchema = {
      refresh_token: refreshToken,
    };

    return await getAuthenticationApiClient().hollyHollyApiCustomAuthViewsLogout(
      {
        refreshTokenSchema,
      },
    );
  } catch (error) {
    throw error;
  }
}

export async function requestPasswordReset(
  email: string,
): Promise<MessageSchema> {
  try {
    const passwordResetRequestSchema: PasswordResetRequestSchema = {
      email: email,
    };

    return await getAuthenticationApiClient().hollyHollyApiCustomAuthViewsPasswordResetRequest(
      {
        passwordResetRequestSchema,
      },
    );
  } catch (error) {
    throw error;
  }
}

export async function confirmPasswordReset(
  uidb64: string,
  token: string,
  newPassword: string,
): Promise<MessageSchema> {
  try {
    const passwordResetConfirmSchema: PasswordResetConfirmSchema = {
      uidb64: uidb64,
      token: token,
      new_password: newPassword,
    };

    return await getAuthenticationApiClient().hollyHollyApiCustomAuthViewsPasswordResetConfirm(
      {
        passwordResetConfirmSchema,
      },
    );
  } catch (error) {
    throw error;
  }
}
