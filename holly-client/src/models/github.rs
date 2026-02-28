use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitRepositoryResponse {
    pub id: String,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub full_name: Option<String>,
    #[serde(default)]
    pub owner: Option<String>,
    #[serde(default)]
    pub url: Option<String>,
    #[serde(default)]
    pub clone_url: Option<String>,
    #[serde(default)]
    pub private: Option<bool>,
    #[serde(default)]
    pub default_branch: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubOAuthInitiateRequest {
    pub redirect_url: String,
    #[serde(default)]
    pub scopes: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubOAuthInitiateResponse {
    pub oauth_url: String,
    pub state: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubOAuthCallbackRequest {
    pub code: String,
    pub state: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GitHubOAuthCallbackResponse {
    pub success: bool,
    pub message: String,
    #[serde(default)]
    pub account_info: Option<serde_json::Value>,
    #[serde(default)]
    pub redirect_url: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn git_repo_optional_fields() {
        let json = r#"{"id":"repo1"}"#;
        let r: GitRepositoryResponse = serde_json::from_str(json).unwrap();
        assert_eq!(r.id, "repo1");
        assert!(r.name.is_none());
    }

    #[test]
    fn oauth_initiate_response_deserializes() {
        let json = r#"{"oauth_url":"https://github.com/login","state":"xyz"}"#;
        let r: GitHubOAuthInitiateResponse = serde_json::from_str(json).unwrap();
        assert_eq!(r.state, "xyz");
    }
}
