use reqwest::{Client, Method, RequestBuilder, Response, StatusCode};
use serde::{de::DeserializeOwned, Serialize};
use std::sync::Arc;
use tokio::sync::Mutex;
use tracing::{debug, warn};

use crate::auth::TokenStore;
use crate::error::{HollyError, Result};
use crate::models::{TokenRefreshInput, TokenRefreshOutput};

/// Shared HTTP client with automatic JWT Bearer injection and 401 → refresh → retry.
#[derive(Clone)]
pub struct ApiClient {
    pub(crate) http: Client,
    pub(crate) base_url: String,
    pub(crate) tokens: TokenStore,
    refresh_lock: Arc<Mutex<()>>,
}

impl ApiClient {
    pub fn new(base_url: impl Into<String>, tokens: TokenStore) -> Self {
        Self {
            http: Client::builder()
                .timeout(std::time::Duration::from_secs(30))
                .build()
                .expect("Failed to build reqwest Client"),
            base_url: base_url.into().trim_end_matches('/').to_string(),
            tokens,
            refresh_lock: Arc::new(Mutex::new(())),
        }
    }

    pub fn url(&self, path: &str) -> String {
        format!("{}{}", self.base_url, path)
    }

    fn with_auth(&self, builder: RequestBuilder) -> RequestBuilder {
        let token = self.tokens.access_token();
        if token.is_empty() {
            builder
        } else {
            builder.header("Authorization", format!("Bearer {}", token))
        }
    }

    pub async fn get<T: DeserializeOwned>(&self, path: &str) -> Result<T> {
        self.execute_authed::<serde_json::Value, T>(Method::GET, path, None).await
    }

    pub async fn post<B: Serialize, T: DeserializeOwned>(&self, path: &str, body: &B) -> Result<T> {
        let json_body = serde_json::to_value(body).map_err(HollyError::Serde)?;
        self.execute_authed::<serde_json::Value, T>(Method::POST, path, Some(json_body)).await
    }

    pub async fn post_no_auth<B: Serialize, T: DeserializeOwned>(&self, path: &str, body: &B) -> Result<T> {
        let req = self.http.request(Method::POST, self.url(path)).json(body);
        let resp = req.send().await?;
        Self::parse_response(resp).await
    }

    pub async fn patch<B: Serialize, T: DeserializeOwned>(&self, path: &str, body: &B) -> Result<T> {
        let json_body = serde_json::to_value(body).map_err(HollyError::Serde)?;
        self.execute_authed::<serde_json::Value, T>(Method::PATCH, path, Some(json_body)).await
    }

    pub async fn put<B: Serialize, T: DeserializeOwned>(&self, path: &str, body: &B) -> Result<T> {
        let json_body = serde_json::to_value(body).map_err(HollyError::Serde)?;
        self.execute_authed::<serde_json::Value, T>(Method::PUT, path, Some(json_body)).await
    }

    pub async fn delete<T: DeserializeOwned>(&self, path: &str) -> Result<T> {
        self.execute_authed::<serde_json::Value, T>(Method::DELETE, path, None).await
    }

    async fn execute_authed<_B, T: DeserializeOwned>(
        &self,
        method: Method,
        path: &str,
        body: Option<serde_json::Value>,
    ) -> Result<T> {
        if !self.tokens.is_authenticated() {
            return Err(HollyError::NotAuthenticated);
        }

        if self.tokens.access_token_expired() {
            debug!("Access token expired — proactively refreshing");
            self.do_refresh().await?;
        }

        let resp = self.build_request(method.clone(), path, body.as_ref()).send().await?;

        if resp.status() == StatusCode::UNAUTHORIZED {
            warn!("Got 401 — attempting token refresh and retry");
            self.do_refresh().await?;
            let resp2 = self.build_request(method, path, body.as_ref()).send().await?;
            return Self::parse_response(resp2).await;
        }

        Self::parse_response(resp).await
    }

    fn build_request(&self, method: Method, path: &str, body: Option<&serde_json::Value>) -> RequestBuilder {
        let builder = self.with_auth(self.http.request(method, self.url(path)));
        match body {
            Some(b) => builder.json(b),
            None => builder,
        }
    }

    pub(crate) async fn do_refresh(&self) -> Result<()> {
        let _guard = self.refresh_lock.lock().await;

        if !self.tokens.access_token_expired() {
            return Ok(());
        }

        let refresh = self.tokens.refresh_token();
        if refresh.is_empty() {
            self.tokens.clear();
            return Err(HollyError::TokenRefresh("No refresh token available".into()));
        }

        let body = TokenRefreshInput { refresh };
        let resp = self
            .http
            .post(self.url("/_api/token/refresh"))
            .json(&body)
            .send()
            .await?;

        if !resp.status().is_success() {
            let status = resp.status().as_u16();
            let msg = resp.text().await.unwrap_or_default();
            self.tokens.clear();
            return Err(HollyError::TokenRefresh(format!("Refresh failed ({status}): {msg}")));
        }

        let out: TokenRefreshOutput = resp.json().await?;
        let email = self.tokens.email();
        if !out.refresh.is_empty() {
            self.tokens.set(&out.access, &out.refresh, &email);
        } else {
            self.tokens.set_access(&out.access);
        }

        debug!("Token refreshed successfully");
        Ok(())
    }

    pub(crate) async fn parse_response<T: DeserializeOwned>(resp: Response) -> Result<T> {
        let status = resp.status();
        if status.is_success() {
            let bytes = resp.bytes().await?;
            serde_json::from_slice(&bytes).map_err(HollyError::Serde)
        } else {
            let msg = resp.text().await.unwrap_or_default();
            Err(HollyError::Api { status: status.as_u16(), message: msg })
        }
    }

    /// Build a raw authenticated request (for streaming/SSE).
    pub fn raw_request_builder(&self, method: Method, path: &str) -> RequestBuilder {
        self.with_auth(self.http.request(method, self.url(path)))
    }

    pub fn sse_url_with_token(&self, path: &str) -> String {
        let token = self.tokens.access_token();
        if token.is_empty() {
            self.url(path)
        } else {
            let encoded: String = url::form_urlencoded::byte_serialize(token.as_bytes()).collect();
            format!("{}{}?token={}", self.base_url, path, encoded)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::auth::TokenStore;

    fn make_client(base: &str) -> ApiClient {
        ApiClient::new(base, TokenStore::new())
    }

    #[test]
    fn url_construction() {
        let c = make_client("http://localhost:8000");
        assert_eq!(c.url("/_api/holly/missions/"), "http://localhost:8000/_api/holly/missions/");
    }

    #[test]
    fn url_trailing_slash_stripped() {
        let c = make_client("http://localhost:8000/");
        assert_eq!(c.url("/_api/test"), "http://localhost:8000/_api/test");
    }

    #[test]
    fn not_authenticated_check() {
        let c = make_client("http://localhost:8000");
        assert!(!c.tokens.is_authenticated());
    }

    #[test]
    fn sse_url_with_token_appends_query() {
        let store = TokenStore::new();
        store.set("mytoken", "ref", "u@u.com");
        let c = ApiClient::new("http://localhost:8000", store);
        let url = c.sse_url_with_token("/_api/holly/missions/sse/start/123");
        assert!(url.contains("?token="));
        assert!(url.contains("mytoken"));
    }

    #[test]
    fn sse_url_no_token_no_query() {
        let c = make_client("http://localhost:8000");
        let url = c.sse_url_with_token("/_api/holly/missions/sse/start/123");
        assert!(!url.contains("?token="));
    }
}
