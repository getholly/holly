use futures_util::StreamExt;
use reqwest::Method;
use crate::api::{ApiClient, SseStream};
use crate::error::{HollyError, Result};
use crate::models::*;

pub struct MissionService {
    api: ApiClient,
}

impl MissionService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/missions/
    pub async fn list(&self) -> Result<Vec<MissionSummary>> {
        self.api.get("/_api/holly/missions/").await
    }

    /// GET /_api/holly/missions/{id}
    pub async fn get(&self, id: &str) -> Result<MissionDetail> {
        self.api.get(&format!("/_api/holly/missions/{id}")).await
    }

    /// POST /_api/holly/missions/
    pub async fn create(&self, data: MissionCreate) -> Result<MissionDetail> {
        self.api.post("/_api/holly/missions/", &data).await
    }

    /// PATCH /_api/holly/missions/{id}
    pub async fn update(&self, id: &str, data: MissionUpdate) -> Result<MissionDetail> {
        self.api.patch(&format!("/_api/holly/missions/{id}"), &data).await
    }

    /// DELETE /_api/holly/missions/{id}
    pub async fn delete(&self, id: &str) -> Result<GenericResponse> {
        self.api.delete(&format!("/_api/holly/missions/{id}")).await
    }

    /// POST /_api/holly/missions/{id}/start
    pub async fn start(&self, id: &str) -> Result<ContainerStartResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/start"), &serde_json::Value::Null).await
    }

    /// GET /_api/holly/missions/sse/start/{id} — streaming start with SSE events.
    pub async fn start_sse<F>(&self, id: &str, mut on_event: F) -> Result<()>
    where
        F: FnMut(SseEvent),
    {
        let url = self.api.sse_url_with_token(&format!("/_api/holly/missions/sse/start/{id}"));
        let mut stream = SseStream::connect(&self.api.http, &url).await?;
        while let Some(event) = stream.next().await {
            match event {
                Ok(ev) => on_event(ev),
                Err(e) => return Err(e),
            }
        }
        Ok(())
    }

    /// POST /_api/holly/missions/{id}/end
    pub async fn end(&self, id: &str, state: MissionStateUpdate) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/end"), &state).await
    }

    /// POST /_api/holly/missions/{id}/conversation
    pub async fn create_conversation(&self, id: &str, data: MissionConversationCreate) -> Result<ConversationStartResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/conversation"), &data).await
    }

    /// POST /_api/holly/missions/{id}/repositories (add)
    pub async fn add_repositories(&self, id: &str, data: MissionRepositoryAdd) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/repositories"), &data).await
    }

    /// DELETE /_api/holly/missions/{id}/repositories (with body)
    pub async fn remove_repositories(&self, id: &str, data: MissionRepositoryRemove) -> Result<GenericResponse> {
        let resp = self.api
            .raw_request_builder(Method::DELETE, &format!("/_api/holly/missions/{id}/repositories"))
            .json(&data)
            .send()
            .await
            .map_err(HollyError::Http)?;
        ApiClient::parse_response(resp).await
    }

    /// POST /_api/holly/missions/{id}/knowledge (add)
    pub async fn add_knowledge(&self, id: &str, data: MissionKnowledge) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/knowledge"), &data).await
    }

    /// POST /_api/holly/missions/{id}/tools (add)
    pub async fn add_tools(&self, id: &str, data: MissionTool) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/tools"), &data).await
    }

    /// POST /_api/holly/missions/{id}/collaborators (add)
    pub async fn add_collaborators(&self, id: &str, data: MissionCollaborator) -> Result<GenericResponse> {
        self.api.post(&format!("/_api/holly/missions/{id}/collaborators"), &data).await
    }
}
