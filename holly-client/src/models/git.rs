use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WorktreeRequest {
    pub repository_url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub branch: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CommitRequest {
    pub message: String,
    #[serde(default)]
    pub files: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PullRequest {
    pub repository_url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub branch: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PushRequest {
    pub repository_url: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub branch: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepositoryBranchesRequest {
    pub repository_url: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BranchesResponse {
    #[serde(default)]
    pub branches: Vec<String>,
    #[serde(default)]
    pub current: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn branches_response_deserializes() {
        let json = r#"{"branches":["main","dev"],"current":"main"}"#;
        let r: BranchesResponse = serde_json::from_str(json).unwrap();
        assert_eq!(r.branches.len(), 2);
        assert_eq!(r.current, Some("main".into()));
    }

    #[test]
    fn worktree_request_skips_null_branch() {
        let w = WorktreeRequest { repository_url: "https://github.com/org/repo".into(), branch: None };
        let json = serde_json::to_string(&w).unwrap();
        assert!(!json.contains("branch"));
    }
}
