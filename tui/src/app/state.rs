//! Core application state — split into domain sub-structs for clarity.

use tokio::sync::mpsc::UnboundedReceiver;
use holly_client::{HollyClient, TokenStore};
use holly_client::models::*;
use crate::config::Config;

// ---------------------------------------------------------------------------
// Screen / navigation
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
pub enum Screen {
    Login,
    Register,
    ForgotPassword,
    Dashboard,
    Missions,
    MissionDetail(String),
    Chat(String),
    Github,
    Llms,
    Settings,
    Notifications,
    Wizard,
    Loading(String, Box<Screen>),
}

// ---------------------------------------------------------------------------
// Domain sub-structs
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, PartialEq)]
pub enum LoginField { Email, Password }

#[derive(Debug, Default)]
pub struct AuthState {
    pub email: String,
    pub password: String,
    pub register_email: String,
    pub register_password: String,
    pub forgot_email: String,
    pub focused: LoginField,
}

impl Default for LoginField {
    fn default() -> Self { LoginField::Email }
}

#[derive(Debug, Default)]
pub struct DashboardState {
    pub missions_count: usize,
    pub repos_count: usize,
    pub conversations_count: usize,
    pub recent_conversations: Vec<ConversationSummary>,
}

#[derive(Debug, Clone, PartialEq)]
pub enum MissionAction { None, Creating, Starting(String), Deleting(String) }
impl Default for MissionAction { fn default() -> Self { Self::None } }

#[derive(Debug, Default)]
pub struct MissionsState {
    pub list: Vec<MissionSummary>,
    pub selected_idx: usize,
    pub action: MissionAction,
    pub new_name: String,
    pub current: Option<MissionDetail>,
}

/// Whether the chat pane is idle or actively streaming tokens from the backend.
#[derive(Debug, Clone, PartialEq)]
pub enum ChatPhase { Idle, Streaming }
impl Default for ChatPhase { fn default() -> Self { Self::Idle } }

pub struct ChatState {
    pub phase: ChatPhase,
    /// Completed (role, content) messages shown above the input bar.
    pub messages: Vec<(String, String)>,
    /// Text the user is currently typing.
    pub input: String,
    /// Tokens received so far for the in-flight assistant response.
    /// Rendered live while `phase == Streaming`.
    pub streaming_buffer: String,
    pub conversations: Vec<ConversationSummary>,
    pub selected_idx: usize,
    /// Receiving end of the SSE token channel. Drained on every `Tick`.
    pub token_rx: Option<UnboundedReceiver<String>>,
}

impl Default for ChatState {
    fn default() -> Self {
        Self {
            phase: ChatPhase::Idle,
            messages: vec![],
            input: String::new(),
            streaming_buffer: String::new(),
            conversations: vec![],
            selected_idx: 0,
            token_rx: None,
        }
    }
}

#[derive(Debug, Default)]
pub struct GithubState {
    pub repositories: Vec<GitRepositoryResponse>,
    pub selected_idx: usize,
}

#[derive(Debug, Default)]
pub struct LlmState {
    pub llms: Vec<LlmSchema>,
    pub api_keys: Vec<UserLlmApiKey>,
    pub selected_idx: usize,
}

#[derive(Debug, Clone, PartialEq)]
pub enum SettingsTab { General, Llm, Github, About }
impl Default for SettingsTab { fn default() -> Self { Self::General } }

#[derive(Debug)]
pub struct SettingsState {
    pub tab: SettingsTab,
    pub server_url: String,
}

#[derive(Debug, Default)]
pub struct NotificationState {
    pub notifications: Vec<NotificationSchema>,
    pub unread_count: u32,
}

// ---------------------------------------------------------------------------
// Top-level App
// ---------------------------------------------------------------------------

pub struct App {
    pub config: Config,
    pub client: HollyClient,
    pub quit: bool,
    pub current_screen: Screen,
    pub status_msg: Option<String>,
    pub error_msg: Option<String>,

    pub auth: AuthState,
    pub dashboard: DashboardState,
    pub missions: MissionsState,
    pub chat: ChatState,
    pub github: GithubState,
    pub llm: LlmState,
    pub settings: SettingsState,
    pub notifications: NotificationState,
}

impl App {
    pub fn new(config: Config) -> Self {
        let server_url = config.server_url.clone();
        let saved_email = config.saved_email.clone().unwrap_or_default();
        Self {
            client: HollyClient::new(&server_url),
            config,
            quit: false,
            current_screen: Screen::Login,
            status_msg: None,
            error_msg: None,
            auth: AuthState { email: saved_email, ..Default::default() },
            dashboard: DashboardState::default(),
            missions: MissionsState::default(),
            chat: ChatState::default(),
            github: GithubState::default(),
            llm: LlmState::default(),
            settings: SettingsState { tab: SettingsTab::General, server_url },
            notifications: NotificationState::default(),
        }
    }

    pub fn should_quit(&self) -> bool { self.quit }

    pub fn set_error(&mut self, msg: impl Into<String>) {
        self.error_msg = Some(msg.into());
        self.status_msg = None;
    }

    pub fn set_status(&mut self, msg: impl Into<String>) {
        self.status_msg = Some(msg.into());
        self.error_msg = None;
    }

    pub fn clear_messages(&mut self) {
        self.status_msg = None;
        self.error_msg = None;
    }

    pub fn navigate_to(&mut self, screen: Screen) {
        self.current_screen = screen;
        self.clear_messages();
    }

    pub fn list_up(&mut self, len: usize, idx: &mut usize) {
        if len > 0 && *idx > 0 { *idx -= 1; }
    }

    pub fn list_down(&mut self, len: usize, idx: &mut usize) {
        if len > 0 && *idx < len - 1 { *idx += 1; }
    }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    fn make_app() -> App { App::new(Config::default()) }

    #[test]
    fn new_app_starts_on_login() {
        assert_eq!(make_app().current_screen, Screen::Login);
    }

    #[test]
    fn new_app_not_authenticated() {
        assert!(!make_app().client.is_authenticated());
    }

    #[test]
    fn auth_state_defaults() {
        let app = make_app();
        assert!(app.auth.password.is_empty());
        assert_eq!(app.auth.focused, LoginField::Email);
    }

    #[test]
    fn missions_state_defaults() {
        let app = make_app();
        assert!(app.missions.list.is_empty());
        assert_eq!(app.missions.selected_idx, 0);
        assert_eq!(app.missions.action, MissionAction::None);
    }

    #[test]
    fn chat_state_defaults() {
        let app = make_app();
        assert_eq!(app.chat.phase, ChatPhase::Idle);
        assert!(app.chat.messages.is_empty());
        assert!(app.chat.token_rx.is_none());
    }

    #[test]
    fn set_error_clears_status() {
        let mut app = make_app();
        app.set_status("OK");
        app.set_error("Oops");
        assert!(app.status_msg.is_none());
        assert_eq!(app.error_msg, Some("Oops".into()));
    }

    #[test]
    fn set_status_clears_error() {
        let mut app = make_app();
        app.set_error("Bad");
        app.set_status("Good");
        assert!(app.error_msg.is_none());
        assert_eq!(app.status_msg, Some("Good".into()));
    }

    #[test]
    fn navigate_clears_messages() {
        let mut app = make_app();
        app.set_error("err");
        app.navigate_to(Screen::Dashboard);
        assert_eq!(app.current_screen, Screen::Dashboard);
        assert!(app.error_msg.is_none());
    }

    #[test]
    fn list_up_clamps_at_zero() {
        let mut app = make_app();
        let mut idx = 0usize;
        app.list_up(5, &mut idx);
        assert_eq!(idx, 0);
    }

    #[test]
    fn list_down_clamps_at_max() {
        let mut app = make_app();
        let mut idx = 4usize;
        app.list_down(5, &mut idx);
        assert_eq!(idx, 4);
    }

    #[test]
    fn list_down_advances() {
        let mut app = make_app();
        let mut idx = 2usize;
        app.list_down(5, &mut idx);
        assert_eq!(idx, 3);
    }

    #[test]
    fn should_quit_initially_false() {
        assert!(!make_app().should_quit());
    }
}
