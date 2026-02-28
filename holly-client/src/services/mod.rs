/// High-level service layer built on top of `ApiClient`.
/// Each service corresponds to a logical domain (auth, missions, etc.).

mod auth_service;
mod mission_service;
mod conversation_service;
mod github_service;
mod llm_service;
mod knowledge_service;
mod tools_service;
mod notification_service;

pub use auth_service::AuthService;
pub use mission_service::MissionService;
pub use conversation_service::ConversationService;
pub use github_service::GithubService;
pub use llm_service::LlmService;
pub use knowledge_service::KnowledgeService;
pub use tools_service::ToolsService;
pub use notification_service::NotificationService;

use crate::api::ApiClient;
use crate::auth::TokenStore;

/// The top-level client — entry point for the entire library.
///
/// ```rust,no_run
/// use holly_client::HollyClient;
///
/// let client = HollyClient::new("http://localhost:8000");
/// ```
#[derive(Clone)]
pub struct HollyClient {
    api: ApiClient,
}

impl HollyClient {
    pub fn new(base_url: impl Into<String>) -> Self {
        let tokens = TokenStore::new();
        Self { api: ApiClient::new(base_url, tokens) }
    }

    pub fn with_tokens(base_url: impl Into<String>, tokens: TokenStore) -> Self {
        Self { api: ApiClient::new(base_url, tokens) }
    }

    /// Auth service (login, register, logout, password reset).
    pub fn auth(&self) -> AuthService {
        AuthService::new(self.api.clone())
    }

    /// Missions service.
    pub fn missions(&self) -> MissionService {
        MissionService::new(self.api.clone())
    }

    /// Conversations service.
    pub fn conversations(&self) -> ConversationService {
        ConversationService::new(self.api.clone())
    }

    /// GitHub service (repositories, installations, OAuth).
    pub fn github(&self) -> GithubService {
        GithubService::new(self.api.clone())
    }

    /// LLMs + user API keys service.
    pub fn llms(&self) -> LlmService {
        LlmService::new(self.api.clone())
    }

    /// Knowledge base service.
    pub fn knowledge(&self) -> KnowledgeService {
        KnowledgeService::new(self.api.clone())
    }

    /// Tools service.
    pub fn tools(&self) -> ToolsService {
        ToolsService::new(self.api.clone())
    }

    /// Notifications service.
    pub fn notifications(&self) -> NotificationService {
        NotificationService::new(self.api.clone())
    }

    /// Returns true if the user is currently logged in.
    pub fn is_authenticated(&self) -> bool {
        self.api.tokens.is_authenticated()
    }

    /// Returns the stored email address (empty if not logged in).
    pub fn current_email(&self) -> String {
        self.api.tokens.email()
    }

    /// Access the raw token store (e.g., to persist tokens across sessions).
    pub fn token_store(&self) -> &TokenStore {
        &self.api.tokens
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn new_client_not_authenticated() {
        let c = HollyClient::new("http://localhost:8000");
        assert!(!c.is_authenticated());
    }

    #[test]
    fn with_tokens_reflects_state() {
        let tokens = TokenStore::new();
        tokens.set("acc", "ref", "u@u.com");
        let c = HollyClient::with_tokens("http://localhost:8000", tokens);
        assert!(c.is_authenticated());
        assert_eq!(c.current_email(), "u@u.com");
    }
}
