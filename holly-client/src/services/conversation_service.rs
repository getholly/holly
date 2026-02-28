use reqwest::Method;
use futures_util::StreamExt;
use crate::api::ApiClient;
use crate::error::{HollyError, Result};
use crate::models::*;

pub struct ConversationService {
    api: ApiClient,
}

impl ConversationService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/conversations/
    pub async fn list(&self) -> Result<Vec<ConversationSummary>> {
        self.api.get("/_api/holly/conversations/").await
    }

    /// GET /_api/holly/conversations/{id}
    pub async fn get(&self, id: &str) -> Result<Conversation> {
        self.api.get(&format!("/_api/holly/conversations/{id}")).await
    }

    /// GET /_api/holly/conversations/{id}/messages
    pub async fn messages(&self, id: &str) -> Result<Vec<Message>> {
        self.api.get(&format!("/_api/holly/conversations/{id}/messages")).await
    }

    /// POST /_api/holly/conversations/sse/send_message/{id} — streaming send.
    /// Calls `on_token` for each streamed token fragment.
    pub async fn send_message_sse<F>(
        &self,
        conversation_id: &str,
        content: &str,
        mut on_token: F,
    ) -> Result<()>
    where
        F: FnMut(String),
    {
        let body = MessageCreate { content: content.to_string(), role: None };
        let resp = self.api
            .raw_request_builder(
                Method::POST,
                &format!("/_api/holly/conversations/sse/send_message/{conversation_id}"),
            )
            .json(&body)
            .send()
            .await
            .map_err(HollyError::Http)?;

        if !resp.status().is_success() {
            let status = resp.status().as_u16();
            let msg = resp.text().await.unwrap_or_default();
            return Err(HollyError::Api { status, message: msg });
        }

        let mut byte_stream = resp.bytes_stream();
        while let Some(chunk) = byte_stream.next().await {
            let bytes = chunk.map_err(HollyError::Http)?;
            let text = std::str::from_utf8(&bytes).unwrap_or("").to_string();

            for line in text.lines() {
                if let Some(data) = line.strip_prefix("data: ") {
                    if data.trim() == "[DONE]" {
                        return Ok(());
                    }
                    if let Ok(ev) = serde_json::from_str::<SseEvent>(data) {
                        if let Some(token) = ev.token {
                            on_token(token);
                        }
                        if ev.done == Some(true) {
                            return Ok(());
                        }
                    }
                }
            }
        }
        Ok(())
    }
}
