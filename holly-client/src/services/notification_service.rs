use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct NotificationService {
    api: ApiClient,
}

impl NotificationService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/notifications/
    pub async fn list(&self) -> Result<NotificationListResponse> {
        self.api.get("/_api/holly/notifications/").await
    }

    /// GET /_api/holly/notifications/unread_count
    pub async fn unread_count(&self) -> Result<UnreadCountResponse> {
        self.api.get("/_api/holly/notifications/unread_count").await
    }

    /// POST /_api/holly/notifications/{id}/read
    pub async fn mark_read(&self, id: &str) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/notifications/{id}/read"), &serde_json::Value::Null).await
    }

    /// POST /_api/holly/notifications/read_all
    pub async fn mark_all_read(&self) -> Result<GenericResponse> {
        self.api.post("/_api/holly/notifications/read_all", &serde_json::Value::Null).await
    }
}
