//! Keyboard event handlers for each screen.

use crossterm::event::{KeyCode, KeyModifiers};
use anyhow::Result;

use crate::app::state::*;
use crate::events::{AppEvent, is_quit};

impl App {
    /// Dispatch an event to the correct handler based on current screen.
    pub async fn handle_event(&mut self, event: AppEvent) -> Result<()> {
        match event {
            AppEvent::Tick => self.on_tick().await?,
            AppEvent::Key(key) => {
                // Global quit
                if is_quit(&key) {
                    self.quit = true;
                    return Ok(());
                }
                // Global Escape — go back one level
                if key.code == KeyCode::Esc {
                    self.handle_escape();
                    return Ok(());
                }
                match &self.current_screen.clone() {
                    Screen::Login => self.handle_login_key(key).await?,
                    Screen::Register => self.handle_register_key(key).await?,
                    Screen::ForgotPassword => self.handle_forgot_key(key).await?,
                    Screen::Dashboard => self.handle_dashboard_key(key).await?,
                    Screen::Missions => self.handle_missions_key(key).await?,
                    Screen::MissionDetail(id) => {
                        let id = id.clone();
                        self.handle_mission_detail_key(key, &id).await?;
                    }
                    Screen::Chat(conv_id) => {
                        let conv_id = conv_id.clone();
                        self.handle_chat_key(key, &conv_id).await?;
                    }
                    Screen::Github => self.handle_github_key(key).await?,
                    Screen::Llms => self.handle_llms_key(key).await?,
                    Screen::Settings => self.handle_settings_key(key).await?,
                    Screen::Notifications => self.handle_notifications_key(key).await?,
                    Screen::Wizard => self.handle_wizard_key(key).await?,
                    Screen::Loading(..) => {} // ignore input while loading
                }
            }
            AppEvent::Resize(..) => {} // ratatui handles this automatically
        }
        Ok(())
    }

    fn handle_escape(&mut self) {
        match &self.current_screen.clone() {
            Screen::Register | Screen::ForgotPassword => self.navigate_to(Screen::Login),
            Screen::Dashboard => {} // can't escape from dashboard
            Screen::Missions | Screen::Chat(_) | Screen::Github | Screen::Llms |
            Screen::Settings | Screen::Notifications | Screen::Wizard => {
                self.navigate_to(Screen::Dashboard);
            }
            Screen::MissionDetail(_) => self.navigate_to(Screen::Missions),
            _ => {}
        }
    }

    async fn on_tick(&mut self) -> Result<()> {
        // Auto-refresh notification badge every ~30 ticks (6 seconds at 200ms tick)
        // (not implemented in this version — would require a tick counter)
        Ok(())
    }

    // ---------- Login ----------

    async fn handle_login_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Tab => {
                self.login_focused = match self.login_focused {
                    LoginField::Email => LoginField::Password,
                    LoginField::Password => LoginField::Email,
                };
            }
            KeyCode::Enter => {
                if self.login_email.is_empty() || self.login_password.is_empty() {
                    self.set_error("Email and password are required");
                    return Ok(());
                }
                self.set_status("Logging in…");
                match self.client.auth().login(&self.login_email, &self.login_password).await {
                    Ok(_) => {
                        self.set_status("Logged in!");
                        self.load_dashboard().await?;
                        self.navigate_to(Screen::Dashboard);
                    }
                    Err(e) => self.set_error(format!("Login failed: {e}")),
                }
            }
            KeyCode::Char('r') if key.modifiers == KeyModifiers::CONTROL => {
                self.navigate_to(Screen::Register);
            }
            KeyCode::Char('f') if key.modifiers == KeyModifiers::CONTROL => {
                self.navigate_to(Screen::ForgotPassword);
            }
            KeyCode::Char(c) => match self.login_focused {
                LoginField::Email => self.login_email.push(c),
                LoginField::Password => self.login_password.push(c),
            },
            KeyCode::Backspace => match self.login_focused {
                LoginField::Email => { self.login_email.pop(); }
                LoginField::Password => { self.login_password.pop(); }
            },
            _ => {}
        }
        Ok(())
    }

    // ---------- Register ----------

    async fn handle_register_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.register_email.is_empty() || self.register_password.is_empty() {
                    self.set_error("Email and password required");
                    return Ok(());
                }
                match self.client.auth().register(&self.register_email, &self.register_password).await {
                    Ok(_) => {
                        self.set_status("Registered! Please log in.");
                        self.login_email = self.register_email.clone();
                        self.navigate_to(Screen::Login);
                    }
                    Err(e) => self.set_error(format!("Register failed: {e}")),
                }
            }
            KeyCode::Tab => {
                self.login_focused = match self.login_focused {
                    LoginField::Email => LoginField::Password,
                    LoginField::Password => LoginField::Email,
                };
            }
            KeyCode::Char(c) => match self.login_focused {
                LoginField::Email => self.register_email.push(c),
                LoginField::Password => self.register_password.push(c),
            },
            KeyCode::Backspace => match self.login_focused {
                LoginField::Email => { self.register_email.pop(); }
                LoginField::Password => { self.register_password.pop(); }
            },
            _ => {}
        }
        Ok(())
    }

    // ---------- Forgot password ----------

    async fn handle_forgot_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.forgot_email.is_empty() {
                    self.set_error("Email required");
                    return Ok(());
                }
                match self.client.auth().request_password_reset(&self.forgot_email).await {
                    Ok(_) => {
                        self.set_status("Reset email sent (if account exists)");
                        self.navigate_to(Screen::Login);
                    }
                    Err(e) => self.set_error(format!("Error: {e}")),
                }
            }
            KeyCode::Char(c) => self.forgot_email.push(c),
            KeyCode::Backspace => { self.forgot_email.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Dashboard ----------

    async fn handle_dashboard_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('1') | KeyCode::Char('c') => {
                if self.conversations.is_empty() { self.load_conversations().await?; }
                let conv_id = self.conversations.first().map(|c| c.id.clone()).unwrap_or_default();
                self.navigate_to(Screen::Chat(conv_id));
            }
            KeyCode::Char('2') | KeyCode::Char('g') => {
                self.load_repos().await?;
                self.navigate_to(Screen::Github);
            }
            KeyCode::Char('3') | KeyCode::Char('m') => {
                self.load_missions().await?;
                self.navigate_to(Screen::Missions);
            }
            KeyCode::Char('4') | KeyCode::Char('l') => {
                self.load_llms().await?;
                self.navigate_to(Screen::Llms);
            }
            KeyCode::Char('5') | KeyCode::Char('s') => self.navigate_to(Screen::Settings),
            KeyCode::Char('n') => {
                self.load_notifications().await?;
                self.navigate_to(Screen::Notifications);
            }
            KeyCode::Char('w') => self.navigate_to(Screen::Wizard),
            _ => {}
        }
        Ok(())
    }

    // ---------- Missions ----------

    async fn handle_missions_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.missions.len();
                let mut idx = self.selected_mission_idx;
                self.list_up(len, &mut idx);
                self.selected_mission_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.missions.len();
                let mut idx = self.selected_mission_idx;
                self.list_down(len, &mut idx);
                self.selected_mission_idx = idx;
            }
            KeyCode::Enter => {
                if let Some(m) = self.missions.get(self.selected_mission_idx) {
                    let id = m.id.clone();
                    match self.client.missions().get(&id).await {
                        Ok(detail) => {
                            self.current_mission = Some(detail);
                            self.navigate_to(Screen::MissionDetail(id));
                        }
                        Err(e) => self.set_error(format!("Failed to load mission: {e}")),
                    }
                }
            }
            KeyCode::Char('n') => {
                self.mission_action = MissionAction::Creating;
                self.new_mission_name.clear();
            }
            KeyCode::Char('r') => {
                self.load_missions().await?;
                self.set_status("Refreshed");
            }
            _ if self.mission_action == MissionAction::Creating => {
                self.handle_create_mission_input(key).await?;
            }
            _ => {}
        }
        Ok(())
    }

    async fn handle_create_mission_input(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Enter => {
                if self.new_mission_name.is_empty() {
                    self.set_error("Mission name required");
                    return Ok(());
                }
                let name = self.new_mission_name.clone();
                match self.client.missions().create(holly_client::models::MissionCreate {
                    name,
                    description: None,
                    llm_id: None,
                }).await {
                    Ok(m) => {
                        self.set_status(format!("Created mission '{}'", m.name));
                        self.mission_action = MissionAction::None;
                        self.load_missions().await?;
                    }
                    Err(e) => self.set_error(format!("Failed to create: {e}")),
                }
            }
            KeyCode::Esc => {
                self.mission_action = MissionAction::None;
                self.new_mission_name.clear();
            }
            KeyCode::Char(c) => self.new_mission_name.push(c),
            KeyCode::Backspace => { self.new_mission_name.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- Mission Detail ----------

    async fn handle_mission_detail_key(&mut self, key: crossterm::event::KeyEvent, id: &str) -> Result<()> {
        let id = id.to_string();
        match key.code {
            KeyCode::Char('s') => {
                self.set_status("Starting mission…");
                match self.client.missions().start(&id).await {
                    Ok(_) => self.set_status("Mission started!"),
                    Err(e) => self.set_error(format!("Start failed: {e}")),
                }
            }
            KeyCode::Char('e') => {
                match self.client.missions().end(&id, holly_client::models::MissionStateUpdate {
                    state: holly_client::models::MissionState::Completed,
                }).await {
                    Ok(_) => {
                        self.set_status("Mission ended");
                        self.navigate_to(Screen::Missions);
                    }
                    Err(e) => self.set_error(format!("End failed: {e}")),
                }
            }
            KeyCode::Char('c') => {
                // Create conversation and open chat
                match self.client.missions().create_conversation(&id, holly_client::models::MissionConversationCreate {
                    title: None,
                    llm_id: None,
                }).await {
                    Ok(resp) => {
                        let conv_id = resp.conversation_id.unwrap_or_default();
                        self.navigate_to(Screen::Chat(conv_id));
                    }
                    Err(e) => self.set_error(format!("Create conversation failed: {e}")),
                }
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Chat ----------

    async fn handle_chat_key(&mut self, key: crossterm::event::KeyEvent, conv_id: &str) -> Result<()> {
        if self.chat_state == ChatState::Streaming {
            return Ok(()); // ignore input while streaming
        }
        let conv_id = conv_id.to_string();
        match key.code {
            KeyCode::Enter => {
                let msg = self.chat_input.trim().to_string();
                if msg.is_empty() { return Ok(()); }
                self.chat_input.clear();
                self.chat_messages.push(("user".into(), msg.clone()));
                self.chat_state = ChatState::Streaming;
                self.streaming_buffer.clear();

                // Stream response — tokens arrive via callback
                // We clone the App fields we need and spawn a task
                let client = self.client.clone();
                let (tx, mut rx) = tokio::sync::mpsc::unbounded_channel::<String>();

                let conv_id_clone = conv_id.clone();
                let msg_clone = msg.clone();
                tokio::spawn(async move {
                    let _ = client.conversations().send_message_sse(
                        &conv_id_clone,
                        &msg_clone,
                        |token| { let _ = tx.send(token); },
                    ).await;
                    let _ = tx.send("\x00DONE\x00".into()); // sentinel
                });

                // Collect tokens synchronously in a tight loop
                // (in practice this would be an async task updating shared state)
                // For now, accumulate all tokens then render
                let mut full_response = String::new();
                while let Some(token) = rx.recv().await {
                    if token == "\x00DONE\x00" { break; }
                    full_response.push_str(&token);
                }
                self.chat_messages.push(("assistant".into(), full_response));
                self.chat_state = ChatState::Idle;
            }
            KeyCode::Char(c) => self.chat_input.push(c),
            KeyCode::Backspace => { self.chat_input.pop(); }
            _ => {}
        }
        Ok(())
    }

    // ---------- GitHub ----------

    async fn handle_github_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.repositories.len();
                let mut idx = self.selected_repo_idx;
                self.list_up(len, &mut idx);
                self.selected_repo_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.repositories.len();
                let mut idx = self.selected_repo_idx;
                self.list_down(len, &mut idx);
                self.selected_repo_idx = idx;
            }
            KeyCode::Char('r') => {
                self.load_repos().await?;
                self.set_status("Refreshed");
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- LLMs ----------

    async fn handle_llms_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Up | KeyCode::Char('k') => {
                let len = self.llms.len();
                let mut idx = self.selected_llm_idx;
                self.list_up(len, &mut idx);
                self.selected_llm_idx = idx;
            }
            KeyCode::Down | KeyCode::Char('j') => {
                let len = self.llms.len();
                let mut idx = self.selected_llm_idx;
                self.list_down(len, &mut idx);
                self.selected_llm_idx = idx;
            }
            KeyCode::Char('r') => {
                self.load_llms().await?;
                self.set_status("Refreshed");
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Settings ----------

    async fn handle_settings_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Tab => {
                self.settings_tab = match self.settings_tab {
                    SettingsTab::General => SettingsTab::Llm,
                    SettingsTab::Llm => SettingsTab::Github,
                    SettingsTab::Github => SettingsTab::About,
                    SettingsTab::About => SettingsTab::General,
                };
            }
            KeyCode::Enter => {
                if self.settings_tab == SettingsTab::General {
                    self.config.server_url = self.settings_server_url.clone();
                    if let Err(e) = self.config.save() {
                        self.set_error(format!("Save failed: {e}"));
                    } else {
                        self.set_status("Settings saved");
                    }
                }
            }
            KeyCode::Char(c) if self.settings_tab == SettingsTab::General => {
                self.settings_server_url.push(c);
            }
            KeyCode::Backspace if self.settings_tab == SettingsTab::General => {
                self.settings_server_url.pop();
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Notifications ----------

    async fn handle_notifications_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('a') => {
                match self.client.notifications().mark_all_read().await {
                    Ok(_) => {
                        self.set_status("All marked as read");
                        self.load_notifications().await?;
                    }
                    Err(e) => self.set_error(format!("Error: {e}")),
                }
            }
            KeyCode::Char('r') => {
                self.load_notifications().await?;
                self.set_status("Refreshed");
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Wizard ----------

    async fn handle_wizard_key(&mut self, key: crossterm::event::KeyEvent) -> Result<()> {
        match key.code {
            KeyCode::Char('1') => {
                self.load_repos().await?;
                self.navigate_to(Screen::Github);
            }
            KeyCode::Char('2') => {
                self.load_missions().await?;
                self.navigate_to(Screen::Missions);
            }
            KeyCode::Char('3') => {
                self.navigate_to(Screen::Settings);
            }
            _ => {}
        }
        Ok(())
    }

    // ---------- Data loaders ----------

    pub async fn load_dashboard(&mut self) -> Result<()> {
        // Create service handles first to avoid temporaries in join!
        let missions_svc = self.client.missions();
        let github_svc = self.client.github();
        let (missions_res, repos_res) = tokio::join!(
            missions_svc.list(),
            github_svc.list_repositories(),
        );
        self.missions_count = missions_res.map(|v| v.len()).unwrap_or(0);
        self.repos_count = repos_res.map(|v| v.len()).unwrap_or(0);
        Ok(())
    }

    pub async fn load_missions(&mut self) -> Result<()> {
        match self.client.missions().list().await {
            Ok(m) => self.missions = m,
            Err(e) => self.set_error(format!("Load missions failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_conversations(&mut self) -> Result<()> {
        match self.client.conversations().list().await {
            Ok(c) => {
                self.conversations_count = c.len();
                self.recent_conversations = c.iter().take(5).cloned().collect();
                self.conversations = c;
            }
            Err(e) => self.set_error(format!("Load conversations failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_repos(&mut self) -> Result<()> {
        match self.client.github().list_repositories().await {
            Ok(r) => self.repositories = r,
            Err(e) => self.set_error(format!("Load repos failed: {e}")),
        }
        Ok(())
    }

    pub async fn load_llms(&mut self) -> Result<()> {
        let llms_svc = self.client.llms();
        let llms_svc2 = self.client.llms();
        let (llms_res, keys_res) = tokio::join!(
            llms_svc.list(),
            llms_svc2.list_api_keys(),
        );
        self.llms = llms_res.unwrap_or_default();
        self.api_keys = keys_res.unwrap_or_default();
        Ok(())
    }

    pub async fn load_notifications(&mut self) -> Result<()> {
        let notif_svc = self.client.notifications();
        let notif_svc2 = self.client.notifications();
        let (list_res, count_res) = tokio::join!(
            notif_svc.list(),
            notif_svc2.unread_count(),
        );
        if let Ok(list) = list_res {
            self.notification_state.notifications = list.results;
        }
        if let Ok(count) = count_res {
            self.notification_state.unread_count = count.count;
        }
        Ok(())
    }
}
