use serde::{Deserialize, Serialize};

/// POST /_api/token/pair  — request body
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenObtainPairInput {
    pub email: String,
    pub password: String,
}

/// POST /_api/token/pair  — response body
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenObtainPairOutput {
    pub email: String,
    pub access: String,
    pub refresh: String,
}

/// POST /_api/token/refresh  — request body
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenRefreshInput {
    pub refresh: String,
}

/// POST /_api/token/refresh  — response body
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TokenRefreshOutput {
    pub access: String,
    pub refresh: String,
}

/// POST /_api/auth/register/
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserSignup {
    pub email: String,
    pub password: String,
}

/// Response for user endpoints
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserResponse {
    pub id: Option<String>,
    pub email: String,
}

/// GET /_api/auth/me/
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserDetail {
    pub id: Option<String>,
    pub email: String,
    #[serde(default)]
    pub first_name: Option<String>,
    #[serde(default)]
    pub last_name: Option<String>,
}

/// POST /_api/auth/logout/
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RefreshTokenSchema {
    pub refresh_token: String,
}

/// POST /_api/auth/password-reset/request/
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PasswordResetRequest {
    pub email: String,
}

/// POST /_api/auth/password-reset/confirm/
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PasswordResetConfirm {
    pub uidb64: String,
    pub token: String,
    pub new_password: String,
}

/// Generic message response
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageResponse {
    pub message: String,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn token_obtain_pair_input_serializes() {
        let input = TokenObtainPairInput {
            email: "test@example.com".into(),
            password: "secret".into(),
        };
        let json = serde_json::to_string(&input).unwrap();
        assert!(json.contains("\"email\":\"test@example.com\""));
        assert!(json.contains("\"password\":\"secret\""));
    }

    #[test]
    fn token_obtain_pair_output_deserializes() {
        let json = r#"{"email":"test@example.com","access":"acc","refresh":"ref"}"#;
        let out: TokenObtainPairOutput = serde_json::from_str(json).unwrap();
        assert_eq!(out.email, "test@example.com");
        assert_eq!(out.access, "acc");
        assert_eq!(out.refresh, "ref");
    }

    #[test]
    fn token_refresh_input_serializes() {
        let input = TokenRefreshInput { refresh: "mytoken".into() };
        let json = serde_json::to_string(&input).unwrap();
        assert!(json.contains("\"refresh\":\"mytoken\""));
    }

    #[test]
    fn token_refresh_output_deserializes() {
        let json = r#"{"access":"newacc","refresh":"newref"}"#;
        let out: TokenRefreshOutput = serde_json::from_str(json).unwrap();
        assert_eq!(out.access, "newacc");
    }

    #[test]
    fn user_detail_optional_fields() {
        let json = r#"{"email":"u@example.com"}"#;
        let user: UserDetail = serde_json::from_str(json).unwrap();
        assert_eq!(user.email, "u@example.com");
        assert!(user.first_name.is_none());
    }
}
