use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ToolSchema {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub enabled: Option<bool>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn tool_schema_deserializes() {
        let json = r#"{"id":"t1","name":"bash","description":"Run bash commands","enabled":true}"#;
        let t: ToolSchema = serde_json::from_str(json).unwrap();
        assert_eq!(t.name, "bash");
        assert_eq!(t.enabled, Some(true));
    }
}
