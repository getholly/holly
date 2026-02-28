use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct LlmService {
    api: ApiClient,
}

impl LlmService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/llms/
    pub async fn list(&self) -> Result<Vec<LlmSchema>> {
        self.api.get("/_api/holly/llms/").await
    }

    /// GET /_api/holly/llms/{id}
    pub async fn get(&self, id: &str) -> Result<LlmSchema> {
        self.api.get(&format!("/_api/holly/llms/{id}")).await
    }

    /// POST /_api/holly/llms/
    pub async fn create(&self, data: LlmCreate) -> Result<LlmSchema> {
        self.api.post("/_api/holly/llms/", &data).await
    }

    /// PATCH /_api/holly/llms/{id}
    pub async fn update(&self, id: &str, data: LlmUpdate) -> Result<LlmSchema> {
        self.api.patch(&format!("/_api/holly/llms/{id}"), &data).await
    }

    /// DELETE /_api/holly/llms/{id}
    pub async fn delete(&self, id: &str) -> Result<GenericResponse> {
        self.api.delete(&format!("/_api/holly/llms/{id}")).await
    }

    // --- User LLM API Keys ---

    /// GET /_api/holly/llmkeys
    pub async fn list_api_keys(&self) -> Result<Vec<UserLlmApiKey>> {
        self.api.get("/_api/holly/llmkeys").await
    }

    /// POST /_api/holly/llmkeys
    pub async fn create_api_key(&self, data: UserLlmApiKeyCreate) -> Result<UserLlmApiKey> {
        self.api.post("/_api/holly/llmkeys", &data).await
    }

    /// PATCH /_api/holly/llmkeys/{id}
    pub async fn update_api_key(&self, id: &str, data: UserLlmApiKeyUpdate) -> Result<UserLlmApiKey> {
        self.api.patch(&format!("/_api/holly/llmkeys/{id}"), &data).await
    }

    /// DELETE /_api/holly/llmkeys/{id}
    pub async fn delete_api_key(&self, id: &str) -> Result<GenericResponse> {
        self.api.delete(&format!("/_api/holly/llmkeys/{id}")).await
    }
}
