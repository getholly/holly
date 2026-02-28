use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationSummary {
    pub id: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub updated_at: Option<String>,
    #[serde(default)]
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Conversation {
    pub id: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub messages: Vec<Message>,
    #[serde(default)]
    pub created_at: Option<String>,
    #[serde(default)]
    pub updated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum MessageRole {
    User,
    Assistant,
    System,
    #[serde(other)]
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Message {
    pub id: String,
    pub role: MessageRole,
    pub content: String,
    #[serde(default)]
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MessageCreate {
    pub content: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub role: Option<String>,
}

/// SSE event emitted during streaming chat
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SseEvent {
    #[serde(default)]
    pub event: Option<String>,
    #[serde(default)]
    pub data: Option<String>,
    #[serde(default)]
    pub token: Option<String>,
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub done: Option<bool>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn conversation_summary_deserializes() {
        let json = r#"{"id":"conv1","title":"Hello"}"#;
        let c: ConversationSummary = serde_json::from_str(json).unwrap();
        assert_eq!(c.id, "conv1");
    }

    #[test]
    fn message_role_deserializes_unknown() {
        let json = r#"{"id":"1","role":"tool","content":"hello"}"#;
        let m: Message = serde_json::from_str(json).unwrap();
        assert_eq!(m.role, MessageRole::Unknown);
    }

    #[test]
    fn message_create_skips_null_role() {
        let mc = MessageCreate { content: "hi".into(), role: None };
        let json = serde_json::to_string(&mc).unwrap();
        assert!(!json.contains("role"));
    }

    #[test]
    fn sse_event_partial_deserializes() {
        let json = r#"{"token":"Hello"}"#;
        let ev: SseEvent = serde_json::from_str(json).unwrap();
        assert_eq!(ev.token, Some("Hello".into()));
        assert!(ev.done.is_none());
    }
}
