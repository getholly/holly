use thiserror::Error;

pub type Result<T> = std::result::Result<T, HollyError>;

#[derive(Error, Debug)]
pub enum HollyError {
    #[error("HTTP request failed: {0}")]
    Http(#[from] reqwest::Error),

    #[error("JSON serialization/deserialization error: {0}")]
    Serde(#[from] serde_json::Error),

    #[error("Authentication error: {0}")]
    Auth(String),

    #[error("Not authenticated — call login() first")]
    NotAuthenticated,

    #[error("Token refresh failed: {0}")]
    TokenRefresh(String),

    #[error("API error {status}: {message}")]
    Api { status: u16, message: String },

    #[error("SSE stream error: {0}")]
    Sse(String),

    #[error("Invalid URL: {0}")]
    Url(#[from] url::ParseError),

    #[error("Unexpected error: {0}")]
    Other(String),
}

impl HollyError {
    pub fn is_auth_error(&self) -> bool {
        matches!(self, HollyError::Auth(_) | HollyError::NotAuthenticated | HollyError::TokenRefresh(_))
    }

    pub fn is_unauthorized(&self) -> bool {
        matches!(self, HollyError::Api { status: 401, .. })
    }
}
