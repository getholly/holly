//! Core application state.

use holly_client::{HollyClient, TokenStore};
use holly_client::models::*;
use crate::config::Config;

/// Which screen is currently displayed — mirrors the Svelte route hierarchy.
#[derive(Debug, Clone, PartialEq)]
pub enum Screen {
    Login,
    Register,
    ForgotPassword,
    Dashboard,
    Missions,
    MissionDetail(String), // mission id
    Chat(String),          // conversation id
    Github,
    Llms,
    Settings,
    Notifications,
    Wizard,
    Loading(String, Box<Screen>), // loading message + screen to go to after
}

/// Which input field is focused on the login screen.
#[derive(Debug, Clone, PartialEq)]
pub enum LoginField {
    Email,
    Password,
}

/// Which action is being performed on a mission.
#[derive(Debug, Clone, PartialEq)]
pub enum MissionAction {
    None,
    Creating,
    Starting(String),
    Deleting(String),
}

/// Chat panel state.
#[derive(Debug, Clone, PartialEq)]
pub enum ChatState {
    Idle,
    Streaming,
}

/// Settings tab.
#[derive(Debug, Clone, PartialEq)]
pub enum SettingsTab {
    General,
    Llm,
    Github,
    About,
}

/// Notification panel state.
#[derive(Debug, Clone, Default)]
pub struct NotificationState {
    pub notifications: Vec<NotificationSchema>,
    pub unread_count: u32,
}

/// Top-level application state.
pub struct App {
    // --- Core ---
    pub config: Config,
    pub client: HollyClient,
    pub quit: bool,
    pub current_screen: Screen,
    pub status_msg: Option<String>,
    pub error_msg: Option<String>,

    // --- Login / Auth ---
    pub login_email: String,
    pub login_password: String,
    pub login_focused: LoginField,
    pub register_email: String,
    pub register_password: String,
    pub forgot_email: String,

    // --- Dashboard ---
    pub missions_count: usize,
    pub repos_count: usize,
    pub conversations_count: usize,
    pub recent_conversations: Vec<ConversationSummary>,

    // --- Missions ---
    pub missions: Vec<MissionSummary>,
    pub selected_mission_idx: usize,
    pub mission_action: MissionAction,
    pub new_mission_name: String,
    pub current_mission: Option<MissionDetail>,

    // --- Chat ---
    pub chat_state: ChatState,
    pub chat_messages: Vec<(String, String)>, // (role, content)
    pub chat_input: String,
    pub streaming_buffer: String,
    pub conversations: Vec<ConversationSummary>,
    pub selected_conversation_idx: usize,

    // --- GitHub ---
    pub repositories: Vec<GitRepositoryResponse>,
    pub selected_repo_idx: usize,

    // --- LLMs ---
    pub llms: Vec<LlmSchema>,
    pub selected_llm_idx: usize,
    pub api_keys: Vec<UserLlmApiKey>,

    // --- Settings ---
    pub settings_tab: SettingsTab,
    pub settings_server_url: String,

    // --- Notifications ---
    pub notification_state: NotificationState,
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

            login_email: saved_email,
            login_password: String::new(),
            login_focused: LoginField::Email,
            register_email: String::new(),
            register_password: String::new(),
            forgot_email: String::new(),

            missions_count: 0,
            repos_count: 0,
            conversations_count: 0,
            recent_conversations: vec![],

            missions: vec![],
            selected_mission_idx: 0,
            mission_action: MissionAction::None,
            new_mission_name: String::new(),
            current_mission: None,

            chat_state: ChatState::Idle,
            chat_messages: vec![],
            chat_input: String::new(),
            streaming_buffer: String::new(),
            conversations: vec![],
            selected_conversation_idx: 0,

            repositories: vec![],
            selected_repo_idx: 0,

            llms: vec![],
            selected_llm_idx: 0,
            api_keys: vec![],

            settings_tab: SettingsTab::General,
            settings_server_url: server_url,

            notification_state: NotificationState::default(),
        }
    }

    pub fn should_quit(&self) -> bool {
        self.quit
    }

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

    /// Move selection up in a list.
    pub fn list_up(&mut self, len: usize, idx: &mut usize) {
        if len > 0 && *idx > 0 {
            *idx -= 1;
        }
    }

    /// Move selection down in a list.
    pub fn list_down(&mut self, len: usize, idx: &mut usize) {
        if len > 0 && *idx < len - 1 {
            *idx += 1;
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn make_app() -> App {
        App::new(Config::default())
    }

    #[test]
    fn new_app_starts_on_login() {
        let app = make_app();
        assert_eq!(app.current_screen, Screen::Login);
    }

    #[test]
    fn new_app_not_authenticated() {
        let app = make_app();
        assert!(!app.client.is_authenticated());
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
    fn list_up_wraps_at_zero() {
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
        let app = make_app();
        assert!(!app.should_quit());
    }
}
