use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationSchema {
    pub id: String,
    #[serde(default)]
    pub message: Option<String>,
    #[serde(default)]
    pub read: Option<bool>,
    #[serde(default)]
    pub created_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NotificationListResponse {
    pub results: Vec<NotificationSchema>,
    #[serde(default)]
    pub count: Option<u32>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnreadCountResponse {
    pub count: u32,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn notification_deserializes() {
        let json = r#"{"id":"n1","message":"Mission completed","read":false}"#;
        let n: NotificationSchema = serde_json::from_str(json).unwrap();
        assert_eq!(n.read, Some(false));
    }

    #[test]
    fn notification_list_response_deserializes() {
        let json = r#"{"results":[],"count":0}"#;
        let r: NotificationListResponse = serde_json::from_str(json).unwrap();
        assert!(r.results.is_empty());
    }
}
