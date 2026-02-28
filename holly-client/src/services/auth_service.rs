use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct AuthService {
    api: ApiClient,
}

impl AuthService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// POST /_api/token/pair — login with email + password.
    pub async fn login(&self, email: &str, password: &str) -> Result<TokenObtainPairOutput> {
        let body = TokenObtainPairInput {
            email: email.to_string(),
            password: password.to_string(),
        };
        let out: TokenObtainPairOutput = self.api.post_no_auth("/_api/token/pair", &body).await?;
        // Store tokens
        self.api.tokens.set(&out.access, &out.refresh, &out.email);
        Ok(out)
    }

    /// POST /_api/auth/register/
    pub async fn register(&self, email: &str, password: &str) -> Result<UserResponse> {
        let body = UserSignup {
            email: email.to_string(),
            password: password.to_string(),
        };
        self.api.post_no_auth("/_api/auth/register/", &body).await
    }

    /// POST /_api/auth/logout/
    pub async fn logout(&self) -> Result<MessageResponse> {
        let refresh = self.api.tokens.refresh_token();
        let body = RefreshTokenSchema { refresh_token: refresh };
        let result: Result<MessageResponse> = self.api.post("/_api/auth/logout/", &body).await;
        self.api.tokens.clear();
        result
    }

    /// GET /_api/auth/me/
    pub async fn me(&self) -> Result<UserDetail> {
        self.api.get("/_api/auth/me/").await
    }

    /// POST /_api/auth/password-reset/request/
    pub async fn request_password_reset(&self, email: &str) -> Result<MessageResponse> {
        let body = PasswordResetRequest { email: email.to_string() };
        self.api.post_no_auth("/_api/auth/password-reset/request/", &body).await
    }

    /// POST /_api/auth/password-reset/confirm/
    pub async fn confirm_password_reset(
        &self,
        uidb64: &str,
        token: &str,
        new_password: &str,
    ) -> Result<MessageResponse> {
        let body = PasswordResetConfirm {
            uidb64: uidb64.to_string(),
            token: token.to_string(),
            new_password: new_password.to_string(),
        };
        self.api.post_no_auth("/_api/auth/password-reset/confirm/", &body).await
    }
}
