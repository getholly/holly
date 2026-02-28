use parking_lot::RwLock;
use std::sync::Arc;
use crate::auth::jwt::is_token_expired;

/// Thread-safe store for JWT access + refresh tokens.
/// Shared via `Arc<TokenStore>` across all service/api instances.
#[derive(Debug, Default)]
pub struct TokenStore {
    inner: Arc<RwLock<Tokens>>,
}

#[derive(Debug, Default, Clone)]
struct Tokens {
    access: String,
    refresh: String,
    email: String,
}

impl TokenStore {
    pub fn new() -> Self {
        Self::default()
    }

    /// Store both tokens after a successful login / refresh.
    pub fn set(&self, access: impl Into<String>, refresh: impl Into<String>, email: impl Into<String>) {
        let mut inner = self.inner.write();
        inner.access = access.into();
        inner.refresh = refresh.into();
        inner.email = email.into();
    }

    pub fn set_access(&self, access: impl Into<String>) {
        self.inner.write().access = access.into();
    }

    pub fn access_token(&self) -> String {
        self.inner.read().access.clone()
    }

    pub fn refresh_token(&self) -> String {
        self.inner.read().refresh.clone()
    }

    pub fn email(&self) -> String {
        self.inner.read().email.clone()
    }

    pub fn is_authenticated(&self) -> bool {
        !self.inner.read().access.is_empty()
    }

    /// Returns true if the access token is missing or JWT exp has passed.
    pub fn access_token_expired(&self) -> bool {
        let access = self.inner.read().access.clone();
        is_token_expired(&access)
    }

    /// Clear all stored tokens (logout).
    pub fn clear(&self) {
        let mut inner = self.inner.write();
        inner.access = String::new();
        inner.refresh = String::new();
        inner.email = String::new();
    }
}

impl Clone for TokenStore {
    fn clone(&self) -> Self {
        TokenStore { inner: Arc::clone(&self.inner) }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn initially_not_authenticated() {
        let store = TokenStore::new();
        assert!(!store.is_authenticated());
    }

    #[test]
    fn set_makes_authenticated() {
        let store = TokenStore::new();
        store.set("acc123", "ref456", "user@test.com");
        assert!(store.is_authenticated());
        assert_eq!(store.access_token(), "acc123");
        assert_eq!(store.refresh_token(), "ref456");
        assert_eq!(store.email(), "user@test.com");
    }

    #[test]
    fn clear_removes_auth() {
        let store = TokenStore::new();
        store.set("acc", "ref", "e@e.com");
        store.clear();
        assert!(!store.is_authenticated());
        assert!(store.access_token().is_empty());
    }

    #[test]
    fn clone_shares_state() {
        let store = TokenStore::new();
        let clone = store.clone();
        store.set("acc", "ref", "e@e.com");
        assert_eq!(clone.access_token(), "acc");
    }

    #[test]
    fn empty_access_is_expired() {
        let store = TokenStore::new();
        assert!(store.access_token_expired());
    }
}
