use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KnowledgeSchema {
    pub id: String,
    pub title: String,
    #[serde(default)]
    pub content: Option<String>,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub created_at: Option<String>,
    #[serde(default)]
    pub updated_at: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn knowledge_schema_deserializes() {
        let json = r#"{"id":"k1","title":"Rust basics"}"#;
        let k: KnowledgeSchema = serde_json::from_str(json).unwrap();
        assert_eq!(k.title, "Rust basics");
        assert!(k.content.is_none());
    }
}
