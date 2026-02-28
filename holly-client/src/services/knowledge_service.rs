use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct KnowledgeService {
    api: ApiClient,
}

impl KnowledgeService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/knowledge/
    pub async fn list(&self) -> Result<Vec<KnowledgeSchema>> {
        self.api.get("/_api/holly/knowledge/").await
    }

    /// GET /_api/holly/knowledge/{id}
    pub async fn get(&self, id: &str) -> Result<KnowledgeSchema> {
        self.api.get(&format!("/_api/holly/knowledge/{id}")).await
    }
}
