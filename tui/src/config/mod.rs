use serde::{Deserialize, Serialize};
use std::path::PathBuf;

/// Persisted configuration for the TUI — stored in ~/.config/holly-tui/config.json
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    pub server_url: String,
    pub theme: Theme,
    #[serde(default)]
    pub saved_email: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum Theme {
    Dark,
    Light,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            server_url: "http://localhost:8000".into(),
            theme: Theme::Dark,
            saved_email: None,
        }
    }
}

impl Config {
    pub fn config_path() -> Option<PathBuf> {
        dirs::config_dir().map(|d| d.join("holly-tui").join("config.json"))
    }

    pub fn load() -> Self {
        let Some(path) = Self::config_path() else { return Self::default() };
        std::fs::read_to_string(&path)
            .ok()
            .and_then(|s| serde_json::from_str(&s).ok())
            .unwrap_or_default()
    }

    pub fn save(&self) -> anyhow::Result<()> {
        let path = Self::config_path().ok_or_else(|| anyhow::anyhow!("No config dir"))?;
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let json = serde_json::to_string_pretty(self)?;
        std::fs::write(path, json)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn default_config_has_localhost() {
        let c = Config::default();
        assert!(c.server_url.contains("localhost"));
        assert_eq!(c.theme, Theme::Dark);
    }

    #[test]
    fn config_round_trips_json() {
        let c = Config {
            server_url: "https://api.example.com".into(),
            theme: Theme::Light,
            saved_email: Some("u@e.com".into()),
        };
        let json = serde_json::to_string(&c).unwrap();
        let loaded: Config = serde_json::from_str(&json).unwrap();
        assert_eq!(loaded.server_url, c.server_url);
        assert_eq!(loaded.theme, Theme::Light);
        assert_eq!(loaded.saved_email, Some("u@e.com".into()));
    }

    #[test]
    fn config_missing_optional_fields() {
        let json = r#"{"server_url":"http://x","theme":"dark"}"#;
        let c: Config = serde_json::from_str(json).unwrap();
        assert!(c.saved_email.is_none());
    }
}
