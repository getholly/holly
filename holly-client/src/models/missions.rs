use serde::{Deserialize, Serialize};
use crate::models::llm::LlmSummary;

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum MissionState {
    Active,
    Inactive,
    Completed,
    Aborted,
    #[serde(other)]
    Unknown,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionSummary {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub state: Option<MissionState>,
    #[serde(default)]
    pub created_at: Option<String>,
    #[serde(default)]
    pub updated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionDetail {
    pub id: String,
    pub name: String,
    #[serde(default)]
    pub description: Option<String>,
    #[serde(default)]
    pub state: Option<MissionState>,
    #[serde(default)]
    pub llm: Option<LlmSummary>,
    #[serde(default)]
    pub repositories: Vec<MissionRepositoryResponse>,
    #[serde(default)]
    pub knowledge: Vec<MissionKnowledgeItem>,
    #[serde(default)]
    pub tools: Vec<MissionToolItem>,
    #[serde(default)]
    pub collaborators: Vec<MissionUser>,
    #[serde(default)]
    pub conversations: Vec<MissionConversation>,
    #[serde(default)]
    pub created_at: Option<String>,
    #[serde(default)]
    pub updated_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionCreate {
    pub name: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub llm_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionUpdate {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub description: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub llm_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionStateUpdate {
    pub state: MissionState,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionRepositoryResponse {
    pub id: String,
    #[serde(default)]
    pub name: Option<String>,
    #[serde(default)]
    pub full_name: Option<String>,
    #[serde(default)]
    pub url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionKnowledgeItem {
    pub id: String,
    #[serde(default)]
    pub title: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionToolItem {
    pub id: String,
    #[serde(default)]
    pub name: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionUser {
    pub id: String,
    #[serde(default)]
    pub email: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionConversation {
    pub id: String,
    #[serde(default)]
    pub title: Option<String>,
    #[serde(default)]
    pub summary: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionConversationCreate {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub title: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub llm_id: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionConversationUpdate {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub summary: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionRepositoryAdd {
    pub repository_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionRepositoryRemove {
    pub repository_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionRepositorySet {
    pub repository_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionCollaborator {
    pub user_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionKnowledge {
    pub knowledge_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionKnowledgeSet {
    pub knowledge_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionTool {
    pub tool_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MissionToolSet {
    pub tool_ids: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ContainerStartResponse {
    #[serde(default)]
    pub container_id: Option<String>,
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub status: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConversationStartResponse {
    #[serde(default)]
    pub conversation_id: Option<String>,
    #[serde(default)]
    pub message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GenericResponse {
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub success: Option<bool>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn mission_summary_deserializes() {
        let json = r#"{"id":"abc","name":"My Mission"}"#;
        let m: MissionSummary = serde_json::from_str(json).unwrap();
        assert_eq!(m.id, "abc");
        assert_eq!(m.name, "My Mission");
    }

    #[test]
    fn mission_create_serializes_no_nulls() {
        let mc = MissionCreate {
            name: "Test".into(),
            description: None,
            llm_id: None,
        };
        let json = serde_json::to_string(&mc).unwrap();
        assert!(!json.contains("null"));
        assert!(json.contains("\"name\":\"Test\""));
    }

    #[test]
    fn mission_state_deserializes_unknown() {
        let json = r#"{"id":"x","name":"y","state":"running"}"#;
        let m: MissionSummary = serde_json::from_str(json).unwrap();
        assert_eq!(m.state, Some(MissionState::Unknown));
    }

    #[test]
    fn mission_detail_defaults_empty_vecs() {
        let json = r#"{"id":"1","name":"m"}"#;
        let d: MissionDetail = serde_json::from_str(json).unwrap();
        assert!(d.repositories.is_empty());
        assert!(d.tools.is_empty());
    }
}
