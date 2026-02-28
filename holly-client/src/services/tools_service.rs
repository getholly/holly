use crate::api::ApiClient;
use crate::error::Result;
use crate::models::*;

pub struct ToolsService {
    api: ApiClient,
}

impl ToolsService {
    pub fn new(api: ApiClient) -> Self { Self { api } }

    /// GET /_api/holly/tools/
    pub async fn list(&self) -> Result<Vec<ToolSchema>> {
        self.api.get("/_api/holly/tools/").await
    }

    /// GET /_api/holly/tools/{id}
    pub async fn get(&self, id: &str) -> Result<ToolSchema> {
        self.api.get(&format!("/_api/holly/tools/{id}")).await
    }
}
